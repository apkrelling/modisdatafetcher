
[![Testing](https://github.com/apkrelling/get_oceancolor/actions/workflows/test.yml/badge.svg)](https://github.com/apkrelling/get_oceancolor/actions/workflows/test.yml)
[![Linting](https://github.com/apkrelling/get_oceancolor/actions/workflows/lint.yml/badge.svg)](https://github.com/apkrelling/get_oceancolor/actions/workflows/lint.yml)

## Modisdatafetcher
This  is a library to easily get chlorophyll-a data from MODIS. It downloads various time-steps 
of chlorophyll data and subsets them according to the user's time and area of interest.

How it works: it gets the names of data files based on the search parameters, accesses the 
data files via OPeNDAP, subsets the data, and saves the subsetted data in the user's computer.


### USAGE

<!-- TO-DO: add installation instructions -->

This project is under development, but as of now there are three main fuctionalities:

1. Get the opendap urls for the data you're interested in.
2. Access the data (subsetted, if desired).
3. save the data in your local machine.

#### Example usage:

```python
import modisdatafetcher

subset_coords = (-70, -25, -15, 20)

dataset_urls = modisdatafetcher.get_opendap_urls(
    date_min = "2021-11-01 00:00:00",
    date_max = "2022-01-01 00:00:00",
    space_res = "4km",  
    time_res = "MO", 
    subset_coords = subset_coords,
    datadir="../../data",
)

lon, lat, chl, time_start, time_end = modisdatafetcher.get_subsetted_dataset(
    subset_coords, 
    dataset_urls
)

modisdatafetcher.save_dataset(
    lon, 
    lat, 
    chl, 
    time_start, 
    time_end,
    space_res= "4km",
    time_res= "MO",
    subset_coords= subset_coords
)
```


### Troubleshooting:
If you're having issues, you might need to get an account at [Earthdata](https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/earthdata-login). 
Follow the steps to create an account, log in, and then run the script again.
