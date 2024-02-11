[![Testing](https://github.com/apkrelling/get_oceancolor/actions/workflows/test.yml/badge.svg)](https://github.com/apkrelling/get_oceancolor/actions/workflows/test.yml)
[![Linting](https://github.com/apkrelling/get_oceancolor/actions/workflows/lint.yml/badge.svg)](https://github.com/apkrelling/get_oceancolor/actions/workflows/lint.yml)

## Get Oceancolor
This is a script to easily get chlorophyll-a data from MODIS. It downloads various time-steps 
of chlorophyll data and subsets them according to the user's time and area of interest.

How it works: it gets the names of data files based on the search parameters, accesses the 
data files via OPeNDAP, subsets the data, and saves the subsetted data in the user's computer.


### USAGE

make sure you have a github account - MAAAYBE


[Install GitHub CLI](https://github.com/cli/cli#installation) in your machine


Fork the repo to your local machine

`gh repo fork REPOSITORY`

Copy the files - MAYBE


Create your environment

`conda env create -f environment.yml`

activate the environment

`conda activate get_oceancolor`

Then you edit the get_oceancolor.py file with the info of the data you'd like to access and download. Run the script. Your data should be saved in the data folder.

### Troubleshooting:
If you're having issues, you might need to get an account at [Earthdata](https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/earthdata-login). 
Follow the steps to create an account, log in, and then run the script again.
