#!/usr/bin/env python
#Python3
# coding: utf-8

import sys
import os
import re
import argparse
import textwrap
import pandas as pd
from bs4 import BeautifulSoup as bs
import time
from selenium import webdriver # necessary due to limitation of BeautifulSoup (i.e. unable to extra JS dynamic tables).
from selenium.webdriver.chrome.options import Options # necessary due to limitation of BeautifulSoup (i.e. unable to extra JS dynamic tables).
import requests
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from IPython.display import display

parser = argparse.ArgumentParser(
        prog='ProgramName',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Scrapes 2021 Los Angeles weather, space weather anomalies and crime data to identify key trends and correlations

        References:  
        https://www.ncei.noaa.gov/cdo-web/search (Data source # 1, .CSV obtained via download)
        https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8/explore/query/ (Data source # 2, web scraping using Beautiful Soup and Selenium to extract data from dynamic JS tables)
        https://api.nasa.gov/DONKI/ (Data source # 3 from NASAs public API, DONKI focuses on space weather events)
        https://www.ncei.noaa.gov/pub/data/cdo/documentation/LCD_documentation.pdf (NOAA Weather Acronym descriptions)
        https://www.nasa.gov/mission_pages/sunearth/news/classify-flares.html (NASA documentation on classification of Solar Flares)
        https://svs.gsfc.nasa.gov/10109 (NASA documentation of Solar Flare scale)
        https://www.swpc.noaa.gov/products/planetary-k-index (NOAA documentation of Geomagnetic Storms)

        AWND = Average Daily Wind Speed (MPH).
        PRCP = Precipitation (inches).
        TMAX = Max Temperature (Fahrenheit).
        TMIN = Min Temperature (Fahrenheit).
        WDF2 = Direction of fastest 2-minute wind (compass degrees).
        WDF5 = Direction of fastest 5-second wind (compass degrees).
        WSF2 = Fastest 2-minute wind speed (MPH).
        WSF5 = Fastest 5-second wind speed (MPH).
        WT01 = Fog, ice fog, or freezing fog (may include heavy fog).
        WT02 = Heavy fog or heavy freezing fog (not always distinguished from fog).
        WT08 = Smoke or haze.
        CRIME = Total number of crime reports received by Los Angeles on a given day during 2021.
        FLR Class = [A, B, C, M, and X], represents strength of a Solar Flare.  Strength increases 10-fold between each letter, with "A-class" being the weakest strength.
        FLR Scale = [1-9], represents finer scale of strength within a specific Solar Flare class (e.g. A-class).
        GST Index = [0-9], represents the Planetary K-index to characterize Geomagnetic Storms, with 9 being the strongest.
        CME Class = [A, B, C, M, and X], represents strength of a Coronal Mass Ejection.  Strength increases 10-fold between each letter, with "A-class" being the weakest strength.

        NOTE:  Datafields SNOW, SNWD, TAVG, TOBS, WESD, WESF, WT03, WT05, WT07, WT11 were intentionally excluded due to empty dataset from NOAA.

        '''))
parser.add_argument("--scrape", type=int, choices=range(1,365), help="Invocation of the flag --scrape N prints to standard output the first N entries of the dataset") # restricts N to data range of 1-365
parser.add_argument("--save", type=str, help="Invocation of the flag --save <path_to_dataset> saves the complete scraped dataset into the file passed as the input")   
parser.add_argument("--graph", action='store_true', help="Invocation of the flag --graph displays 9 graphs to interpret datasets from multiple sources")
parser.add_argument("--stats", action='store_true', help="Invocation of the flag --stats datasets existing above and below the mean")
args = parser.parse_args()        

# DEV NOTE - add .ipynb build below this comment.



def main():
    # main function
    global merge
    pd.set_option('display.max_rows', None) # changes Pandas default display limit of 10 to None, so that full dataset can be displayed using show_table()
    pd.set_option('display.max_columns', None) # changes Pandas default display limit of 12 columns to None, so that full dataset can be displayed using show_table()
    try:
        # attempts to retrieve data from .csv, to avoid re-building table
        merge = pd.read_csv('merge.csv', header=0)
        print('Datasets gathered previously.\nLoading from merge.csv\n')
    except:
        # gathers data from sources, builds dataframe
        print('Initializing collection of datasets.\n', '.'*6, 'Please wait.', '.'*6)
        add_weatherdata()
        add_crimedata()
        add_donki()
        merge_frames()
    if args.scrape: # if args.scrape exists, it will print a table of N rows
        show_table(args.scrape) # replace with arg.scrape
    elif args.save: # if args.save exists, it will save the file to a location
        save_csv(args.save)  # replace with arg.save
    elif args.graph: # if args.graph exists, it will print 9 line graphs using data generated
        show_graph()
    elif args.stats: # if args.stats exists, it will print datasets and statistical information based on values existing above and below mean
        show_stats()
    else:
        show_table(365) # if NO sysargs exist, will display full dataset
        print('\n\nNo system arguments provided, please type scraper.py --help for more information')
    
def add_weatherdata():
    # data source 1 (csv)
    global df
    df = pd.read_csv('NOAA Los Angeles County 2021 Daily Weather.csv', header=0)  # builds table from downloaded weather data .CSV
    df['DATE'] = pd.to_datetime(df['DATE']) # requirement to sort by date in a panda dataframe
    df = df.set_index('DATE')
    df = df.drop(df.columns[[0, 1, 2, 3, 4, 6, 7, 8, 10, 11, 12, 15, 18, 19, 24, 25, 26, 28]], axis=1) # removes empty datasets from table & uneccessary static data (e.g. lattitude, longitude)
    print('.'*6, 'Collecting Weather data - 100% Complete', '.'*6)
    
def add_crimedata():
    # data source 2 (web scraping)
    global df
    url_iteration = [['01', '03', '31'], ['04', '06', '30'], ['07', '09', '30'], ['10', '12', '31']] # start & end months for iteration through webpage
    counts = []
    
    for i in range(len(url_iteration)): # iterative query for each quarter of the year, as website has a limitation of showing 100 rows per page    
        s_month = url_iteration[i][0] # retrieves ## of month for start of query
        e_month = url_iteration[i][1] # retrieves ## of month for end of query
        d_e_month = url_iteration[i][2] # retrieves ## for the last day in the month at end of query
        url = 'https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8/explore/query/SELECT%20%60date_occ%60%2C%20count%28%60date_occ%60%29%20AS%20%60count_date_occ%60%0AGROUP%20BY%20%60date_occ%60%0AHAVING%0A%20%20%60date_occ%60%0A%20%20%20%20BETWEEN%20%222021-' + s_month + '-01T00%3A00%3A00%22%20%3A%3A%20floating_timestamp%0A%20%20%20%20AND%20%222021-' + e_month + '-' + d_e_month + 'T23%3A45%3A00%22%20%3A%3A%20floating_timestamp/page/aggregate'
        options = webdriver.ChromeOptions() # adds options to selenium, to reduce terminal spam, minimize launched chrome window
        options.add_argument('headless') # hides chrome in background
        options.add_argument("start-minimized") # hides chrome in background
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('log-level=3') # added to reduce terminal spam.  Log values are:  INFO=0, WARNING=1, LOG_ERROR=2, LOG_FATAL=3.
        browser = webdriver.Chrome(options=options)
        browser.get(url)
        if i == 0: # progress indicator code
            time.sleep(5) # wait 5 seconds to load web-page in chrome using selenium (dynamic JS table), in order for it to be parsed with Beautiful Soup as HTML
            print('.'*6, 'Collecting Crime data - 25% Complete', '.'*6)
        if i == 1:
            time.sleep(5) # wait 5 seconds to load web-page in chrome using selenium (dynamic JS table), in order for it to be parsed with Beautiful Soup as HTML
            print('.'*6, 'Collecting Crime data - 50% Complete', '.'*6)
        if i == 2:
            time.sleep(5) # wait 5 seconds to load web-page in chrome using selenium (dynamic JS table), in order for it to be parsed with Beautiful Soup as HTML
            print('.'*6, 'Collecting Crime data - 75% Complete', '.'*6)
        if i == 3:
            time.sleep(5) # wait 5 seconds to load web-page in chrome using selenium (dynamic JS table), in order for it to be parsed with Beautiful Soup as HTML
        html = browser.page_source
        soup = bs(html, 'lxml')
        table_rows = soup.find_all('td')

        for i in range(len(table_rows)): # iterates through soup by index
            row = str(table_rows[i])
            if i % 2 == 0:
                pass
                #date = re.search(r'success">(?P<date>2021) (?P<month>[a-zA-Z]{1,3}) (?P<day>\d\d)', row) # test to scrape dates
            else:
                count = re.search(r'class="">(?P<crime>\d{1,4})', row) # regex to search soup for table row data, and groups value to be recalled by "crime"
                counts.append(count.group('crime'))
    try: # ADDED try/except block, as sometimes web connection fails to grab all 365 data sets and fails to add to DF
        df = df.assign(CRIME = counts) # ADDs "CRIME" column header to data frame, and 365 values of daily total crime stats to DataFrame
        print('.'*6, 'Collecting Crime data - 100% Complete', '.'*5)
    except:
        print('Web scraping of LA County Crime data 2021 failed, trying again')
        add_crimedata()

def add_donki():
    # data source 3 (API)
    global df_flr, df_gst, df_cme
    api_key = '...' # Replace "..." with your public API key obtained from api.nasa.gov
    url_keys = ['FLR', 'GST', 'CME']
    api_url = 'https://api.nasa.gov/DONKI/{}?startDate=2021-01-01&endDate=2021-12-31&api_key={}'
    flr_date, flr_class, flr_scale = [], [], []
    gst_date, gst_index = [], []
    cme_date, cme_class = [], []
    
    for i in range(len(url_keys)): # iterates through three API calls to retrieve FLR, GST, and CME datasets from DONKI
        html2 = api_url.format(url_keys[i], api_key)
        r1 = requests.get(html2)
        
        if i == 0: # FLR
            for i in range(len(r1.json())):
                tmp = r1.json()[i].get('beginTime')
                flr_date.append(tmp[5:7].lstrip('0') + '/' + tmp[8:10].lstrip('0') + '/' + tmp[0:4])
                tmp = r1.json()[i].get('classType')
                flr_class.append(tmp[0:1])
                flr_scale.append(tmp[1:])
            print('.'*6, 'Collecting Space Weather data - 33% complete', '.'*6) # progress indicator
        if i == 1: # GST
            for i in range(len(r1.json())):
                tmp = r1.json()[i].get('startTime')
                gst_date.append(tmp[5:7].lstrip('0') + '/' + tmp[8:10].lstrip('0') + '/' + tmp[0:4])           
                gst_index.append(r1.json()[i].get('allKpIndex')[0].get('kpIndex'))
            print('.'*6, 'Collecting Space Weather data - 66% complete', '.'*6) # progress indicator
        if i == 2: # CME
            for i in range(len(r1.json())):
                if r1.json()[i].get('cmeAnalyses') != None: # excludes empty/incomplete datasets found within donki
                    tmp = r1.json()[i].get('startTime')
                    cme_date.append(tmp[5:7].lstrip('0') + '/' + tmp[8:10].lstrip('0') + '/' + tmp[0:4])
                    cme_class.append(r1.json()[i].get('cmeAnalyses')[0].get('type'))
                else:
                    continue
            print('.'*6, 'Collecting Space Weather data - 100% complete', '.'*5) # progress indicator
    
    # build Solar Flare dataframe
    df_flr = pd.DataFrame(list(zip(flr_date, flr_class, flr_scale)), columns=['DATE', 'FLR Class', 'FLR Scale'])
    df_flr['DATE'] = pd.to_datetime(df_flr['DATE']) # requirement to sort by date in a panda dataframe
    df_flr = df_flr.sort_values(by = ['DATE', 'FLR Class', 'FLR Scale'], ascending = [True, True, True])
    df_flr = df_flr.drop_duplicates(subset=['DATE'], keep='last') # removes duplicates, and accepts only the highest reported class/scale event
    df_flr = df_flr.set_index('DATE')
    
    # build Geomagnetic Storm dataframe
    df_gst = pd.DataFrame(list(zip(gst_date, gst_index)), columns=['DATE', 'GST Index'])
    df_gst['DATE'] = pd.to_datetime(df_gst['DATE']) # requirement to sort by date in a panda dataframe
    df_gst = df_gst.set_index('DATE')
    
    # build Coronal Mass Ejection dataframe
    df_cme = pd.DataFrame(list(zip(cme_date, cme_class)), columns=['DATE', 'CME Class'])       
    df_cme['DATE'] = pd.to_datetime(df_cme['DATE']) # requirement to sort by date in a panda dataframe
    df_cme = df_cme.sort_values(by = ['DATE', 'CME Class'], ascending = [True, True])
    df_cme = df_cme.drop_duplicates(subset=['DATE'], keep='last') # removes duplicates, and accepts only the highest reported class event
    df_cme = df_cme.set_index('DATE') 

def merge_frames():
    # Merges Solar Flare, Geomagnetic Storm, and Coronal Mass Ejection dataframes with df into Merge
    global merge, df, df_flr, df_gst, df_cme
    merge = pd.merge(df, df_flr, how="left", on='DATE') # merges dataframes from datasource # 3 into main dataframe (merge)
    merge = pd.merge(merge, df_gst, how="left", on='DATE')
    merge = pd.merge(merge, df_cme, how="left", on='DATE')
    # saves merge dataframe to merge.csv, to reduce overhead when program called repeatedly
    try:
        merge.to_csv(r'merge.csv')
    except:
        pass

def show_graph():
    # called with the --graph system argument, displays 9 graphs of associated datasets.
    
    global merge
    
    print('Building line graphs from 9 distinct datasets.\n', '.'*6, 'Please Wait', '.'*6, '\n')
    
    fig, ax = plt.subplots(9, 1, figsize=(32, 20), tight_layout=True) # [rows, columns]
    fig.subplots_adjust(top=0.8)
    myFmt = mdates.DateFormatter('%b %d')
    
    # graph 1 - Crime vs PRCP
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[0], color='red', label='Crime')
    ax1 = ax[0].twinx() # used to overlay two datasets on the same table
    sns.lineplot(data=merge, x='DATE', y='PRCP', ax=ax1, color='blue', label='PRCP')
    ax[0].set_title("Crime vs Precipitation")
    ax[0].legend(loc='upper right')
    ax1.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80)) # offsets 2nd legend, so as not to overlap
    ax[0].xaxis.set_major_formatter(myFmt)
    ax[0].xaxis.set_major_locator(mdates.MonthLocator(interval=1)) # formats x-axis by month
    ax1.spines["right"].set_color('blue')
    
    # graph 2 - Crime vs TMAX/TMIN
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[1], color='red', label='Crime')
    ax2 = ax[1].twinx()
    sns.lineplot(data=merge, x='DATE', y='TMAX', ax=ax2, color='blue', label='TMAX')
    sns.lineplot(data=merge, x='DATE', y='TMIN', ax=ax2, color='green', label='TMIN')
    ax[1].set_title("Crime vs Temperature Max (TMAX, TMIN)")    
    ax[1].legend(loc='upper right')
    ax2.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[1].xaxis.set_major_formatter(myFmt)
    ax[1].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        
    # graph 3 - Crime vs AWND
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[2], color='red', label='Crime')
    ax4 = ax[2].twinx()
    sns.lineplot(data=merge, x='DATE', y='AWND', ax=ax4, color='blue', label='AWND')
    ax[2].set_title("Crime vs Average Daily Wind Speed (AWND)")    
    ax[2].legend(loc='upper right')
    ax4.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[2].xaxis.set_major_formatter(myFmt)
    ax[2].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax4.spines["right"].set_color('blue')
         
    # graph 4 - Crime vs WSF2/WSF5
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[3], color='red', label='Crime')
    ax5 = ax[3].twinx()
    sns.lineplot(data=merge, x='DATE', y='WSF2', ax=ax5, color='blue', label='WSF2')
    sns.lineplot(data=merge, x='DATE', y='WSF5', ax=ax5, color='green', label='WSF5')
    ax[3].set_title("Crime vs Fastest 2-minute (WSF2) and 5-second (WSF5) wind speed")    
    ax[3].legend(loc='upper right')
    ax5.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[3].xaxis.set_major_formatter(myFmt)
    ax[3].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        
    # graph 5 - Crime vs WT01/WT02
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[4], color='red', label='Crime')
    ax7 = ax[4].twinx()
    sns.lineplot(data=merge, x='DATE', y='WT01', ax=ax7, color='blue', label='WT01')
    sns.lineplot(data=merge, x='DATE', y='WT02', ax=ax7, color='green', label='WT02')
    ax[4].set_title("Crime vs Weather Conditions:  WT01 (fog, ice fog, freezing fog),  WT02 (heavy fog)")    
    ax[4].legend(loc='upper right')
    ax7.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[4].xaxis.set_major_formatter(myFmt)
    ax[4].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        
    # graph 6 - Crime vs WT08
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[5], color='red', label='Crime')
    ax9 = ax[5].twinx()
    sns.lineplot(data=merge, x='DATE', y='WT08', ax=ax9, color='blue', label='WT08')
    ax[5].set_title("Crime vs Weather Condition WT08 (smoke or haze)")    
    ax[5].legend(loc='upper right')
    ax9.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[5].xaxis.set_major_formatter(myFmt)
    ax[5].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax9.spines["right"].set_color('blue')
        
    # graph 7 - Crime vs FLR
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[6], color='red', label='Crime')
    ax10 = ax[6].twinx()
    ax11 = ax[6].twinx()
    sns.lineplot(data=merge, x='DATE', y='FLR Class', ax=ax10, color='blue', label='FLR Class')
    sns.lineplot(data=merge, x='DATE', y='FLR Scale', ax=ax11, color='green', label='FLR Scale')
    ax[6].set_title("Crime vs Solar Flares (FLR Class, FLR Scale)")    
    ax[6].legend(loc='upper right')
    ax10.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax11.legend(loc='upper right', bbox_to_anchor=(1.0, 0.60))
    ax[6].xaxis.set_major_formatter(myFmt)
    ax[6].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax10.spines["right"].set_color('blue')
    ax11.spines["right"].set_color('green')
    ax11.spines["right"].set_position(("axes", +1.025)) # offsets 2nd y-axis
        
    # graph 8 - Crime vs GST
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[7], color='red', label='Crime')
    ax12 = ax[7].twinx()
    sns.lineplot(data=merge, x='DATE', y='GST Index', ax=ax12, color='blue', label='GST Index')
    ax[7].set_title("Crime vs Geomagnetic Storms (GST Index)")    
    ax[7].legend(loc='upper right')
    ax12.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[7].xaxis.set_major_formatter(myFmt)
    ax[7].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax12.spines["right"].set_color('blue')
        
    # graph 9 - Crime vs CME
    sns.lineplot(data=merge, x='DATE', y='CRIME', ax=ax[8], color='red', label='Crime')
    ax13 = ax[8].twinx()
    sns.lineplot(data=merge, x='DATE', y='CME Class', ax=ax13, color='blue', label='CME Class')
    ax[8].set_title("Crime vs Coronal Mass Ejection (CME Class)")    
    ax[8].legend(loc='upper right')
    ax13.legend(loc='upper right', bbox_to_anchor=(1.0, 0.80))
    ax[8].xaxis.set_major_formatter(myFmt)
    ax[8].xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax13.spines["right"].set_color('blue')
        
    fig.suptitle("Daily comparison of local and space weather to crime reports in Los Angeles 2021", y=1.0)
    plt.show()    

def show_stats():
    # called with the --stats system argument, provides datasets above and below the mean for analysis.
    global merge
    merge_above_mean = merge # test dataframe
    merge_below_mean = merge
    mean_values = []
    # includes crime, awnd, prcp, tmax, tmin, wsf2, wsf5, wt01, wt02
    labels = ['CRIME', 'AWND', 'PRCP', 'TMAX', 'TMIN', 'WSF2', 'WSF5', 'WT01', 'WT02', 'FLR Class', 'GST Index', 'CME Class']
    
    for i in range(len(labels)): # iterates through labels to identify mean values for each column in list "labels"
        if i >= 7 and i < 9: # WT01, WT02
            mean_values.append(0) # wt01_mean and wt02_mean NOT needed, as binary value, anything greater than 0
        elif i >= 9: # FLR, GST, CME
            continue # replace with NaN
        else: # CRIME, AWND, PRCP, TMAX, TMIN, WSF2, WSF5
            mean_values.append(merge.loc[:, labels[i]].mean())
    
    for i in range(len(labels)-1): # range of 12-1
        if i < 8:
            # build DF for values above mean
            merge_above_mean = merge
            merge_above_mean = merge_above_mean[merge_above_mean.loc[:, labels[0]] > mean_values[0]] # CRIME above mean
            merge_above_mean = merge_above_mean[merge_above_mean.loc[:, labels[i+1]] > mean_values[i+1]] # second variable above mean
            merge_above_mean.reset_index(drop=True, inplace=True)
            print(f'\n\nThere were {len(merge_above_mean.index)} days where {labels[0]} and {labels[i+1]} were above the mean.')
            
            # build DF for values below mean
            merge_below_mean = merge
            merge_below_mean = merge_below_mean[merge_below_mean.loc[:, labels[0]] > mean_values[0]] # CRIME above mean
            merge_below_mean = merge_below_mean[merge_below_mean.loc[:, labels[i+1]] <= mean_values[i+1]] # second variable below mean
            merge_below_mean.reset_index(drop=True, inplace=True)
            print(f'There were {len(merge_below_mean.index)} days where {labels[0]} and {labels[i+1]} were below the mean.')
            print(f'{labels[0]} mean: {mean_values[0]:.2f}')
            print(f'{labels[i+1]} mean: {mean_values[i+1]:.2f}')
            print(f'\n{labels[0]} and {labels[i+1]} above the mean dataset.')
            display(merge_above_mean)
            print(f'\n{labels[0]} and {labels[i+1]} below the mean dataset.')
            display(merge_below_mean)
            
        else:
            # build DF for values above mean
            merge_above_mean = merge
            merge_above_mean = merge_above_mean[merge_above_mean.loc[:, labels[0]] > mean_values[0]] # CRIME above mean
            merge_above_mean = merge_above_mean[merge_above_mean[labels[i+1]].notna()] # filters on NaN for FLR, GST, CME events
            merge_above_mean.reset_index(drop=True, inplace=True)
            print(f'\n\nThere were {len(merge_above_mean.index)} days where both {labels[0]} and {labels[i+1]} were above the mean.')
            
            # build DF for values below mean
            merge_below_mean = merge
            merge_below_mean = merge_below_mean[merge_below_mean.loc[:, labels[0]] > mean_values[0]] # CRIME above mean
            merge_below_mean = merge_below_mean[merge_below_mean[labels[i+1]].isna()] # filters on NaN for FLR, GST, CME events
            merge_below_mean.reset_index(drop=True, inplace=True)
            print(f'There were {len(merge_below_mean.index)} days where {labels[0]} and {labels[i+1]} were below the mean.')
            print(f'{labels[0]} mean: {mean_values[0]:.2f}')
            print(f'\n{labels[0]} and {labels[i+1]} above the mean dataset.')
            display(merge_above_mean)
            print(f'\n{labels[0]} and {labels[i+1]} below the mean dataset.')
            display(merge_below_mean)
    
def show_table(self):
    # prints N number of rows to the terminal, based on optional sysarg --scrape
    global merge
    display(merge.head(self))

def save_csv(self):
    # saves dataframe (merge) to .CSV, based on optional sysarge --save
    global merge
    try:
        merge.to_csv(self)
        print('Export of dataset successful!')
    except:
        print('Unable to export to .csv, please check permissions')

# DEV note, do NOT change below.
   
if __name__ == '__main__':
    main() # calls main function
