# Data-Science-Project

Graduate Student data science programming project for University of Southern California (USC) Viterbi School of Engineering.

Project intends to gather the following information about Los Angeles during the year of 2021:  Crime, Local Weather, and Space Weather Events.

Project Requirements:
1.	Minimum of 3 data sources
2.	Use of Web Scraping for one data source
3.	Use of a public API for one data source
4.	Use of a .CSV for one data source

Hypothesis:  Is there a correlation between anomalous Local Weather and/or Space Weather events resulting in an increase or decrease in reported crime?

						
# INITIAL SETUP

Save the following files to the same directory:
1.  "scraper.py"
2.  "NOAA Los Angeles County 2021 Daily Weather.CSV"
3.  "readme.txt"
4.  Request public API key from:  https://api.nasa.gov/
5.  Edit "scraper.py"
6.  Navigate to Line 155.
7.  Replace value of variable "api_key" with your NASA public API key
8.  Save and exit


# REQUIRED PACKAGES/MODULES

    NOTE 1:  Script imports modules from a variety of sources and will not function if these modules are not installed.
    NOTE 2:  Script requires Chrome web browser and will not collect data from source # 2 if it is not installed.

Required Python Modules:
1.  sys
2.  os
3.  re
4.  argparse
5.  textwrap
6.  pandas
7.  bs4
8.  time
9.  selenium
10.  requests
11.  json
12.  matplotlib.pyplot
13.  matplotlib.dates
14.  seaborn
15.  IPython

# PYTHON module/package installation:
1.  Open terminal.
2.  Type "pip install [insert module name]".
3.  Repeat step 2 until all required modules have been installed.

# Chrome installation:
1.  Open web browser.
2.  Navigate to https://www.google.com/chrome/.
3.  Download distributable.
4.  Install Chrome.


# OPERATION

    NOTE 4:  Program includes various wait parameters to adequantely load and render websites in a browser in order to scrape data sources
		 # 2 (converts dynamic JS tables (Selenium) to HTML (BeautifulSoup)), and # 3 (DONKI - NASA Public API).  Script will regularly
		 provide status updates throughout operation till completed.

Instructions:
1.  Open terminal.
2.  Navigate to directory where files are saved using the "cd" command.
3.  Type "python scraper.py" to run the script.
4.  Add the "-h" or "--help" arguments to display program description, optional arguments and expected inputs.
5.  Add the "--save" optional argument with a [filename.csv] or [path\file.csv] to save data to a .csv file.
6.  Add the "--scrape" optional argument with an integer [1-365] to print the first N rows of data to the terminal.
7.  Add the "--stats" optional argument to display datasets occurring above or below the mean for analysis.
8.  Add the "--graph" optional argument to display 9 graphs of related datasets for analysis.


# TROUBLESHOOTING
	
Python error:  Unable to install python modules via "pip install".

To resolve this error:
1.  Open terminal with administrator permissions
	

# CHANGELOG 
						
V5:
1.  ADDED - try/except block for add_crimedata(), as an error may occur when web scraping fails to capture all 365 data points and cannot add to dataframe (df)
2.  CHANGED - dataframe (df) to reflect "DATE" as the index_col
3.  ADDED - progress indicator for status of web scraping (i.e. data source # 2)
4.  ADDED - DONKI (NASA Public API) data collection with function add_donki() (i.e. data source # 3)
5.  ADDED - progress indicator for status of API scraping
6.  ADDED - merge dataframes function merge_frames(), which joins data source # 3 to datasources 1 & 2.  First instance of calling merge_frames() will additionally save datasets to a file called merge.csv.  This is independant of the "--save" system argument.
7.  ADDED - try/except block to load data from merge.csv to reduce system overhead in execution of scraper.py instance (n+1) (i.e. only scrapes data during 1st execution).
8.  ADDED - show_graph() function and associated system argument "--stats", to display 9 graphs of related datasets for analysis
9.  UPDATED - "--help" comment references to reflect additional dataframe header labels (FLR Class, FLR Scale, GST Index, and CME Class)
10.  ADDED - show_table(365) added to main() to display full dataset when script is run without --scrape (addresses feedback from part 2 submission)

# REFERENCES

Acronym descriptions:
1.  https://www.ncei.noaa.gov/pub/data/cdo/documentation/LCD_documentation.pdf (NOAA Weather Acronym descriptions)
2.  https://www.nasa.gov/mission_pages/sunearth/news/classify-flares.html (NASA documentation on classification of Solar Flares)
3.  https://svs.gsfc.nasa.gov/10109 (NASA documentation of Solar Flare scale)
4.  https://www.swpc.noaa.gov/products/planetary-k-index (NOAA documentation of Geomagnetic Storms)

Data Source # 1: 
1.  .CSV obtained via download.
2.  https://www.ncei.noaa.gov/cdo-web/search

Data Source # 2:
1.  Beautiful Soup HTML web scraped table from LA City Crime Data
2.  https://bit.ly/3UM89cn
3.  https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8/explore/query/SELECT%20%60date_occ%60%2C%20count%28%60date_occ%60%29%20AS%20%60count_date_occ%60%0AWHERE%0A%20%20%60date_occ%60%0A%20%20%20%20BETWEEN%20%222021-01-01T00%3A00%3A00%22%20%3A%3A%20floating_timestamp%0A%20%20%20%20AND%20%222021-12-31T23%3A45%3A00%22%20%3A%3A%20floating_timestamp%0AGROUP%20BY%20%60date_occ%60/page/filter

Data Source # 3:
1.  Listing of public APIs from NASA
2.  https://api.nasa.gov/
3.  DONKI space weather event tracking, using a NASA API
4.  https://kauai.ccmc.gsfc.nasa.gov/DONKI/search/ 
