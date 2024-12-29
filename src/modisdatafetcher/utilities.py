from __future__ import annotations

import functools
import re
import sys
from datetime import datetime

import netCDF4 as nc
import numpy as np


def debug(func):
    """Print the function signature and return value"""

    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        args_repr = [repr(a) for a in args]  # get args
        kwargs_repr = [f"{key}={val!r}" for key, val in kwargs.items()]  # get kwargs
        signature = ", ".join(args_repr + kwargs_repr)  # print the func called
        print(f"Calling {func.__name__}({signature})")
        value = func(*args, **kwargs)
        print(f"{func.__name__!r} returned {value!r}")  # print the func output
        print(
            f"Data types {[type(item) for item in value]}"
        )  # print the output data types
        return value

    return wrapper_debug


def check_date_format(date: str) -> None:
    """Tests if input has "%Y-%m-%d %H:%M:%S" date format.

    Parameters:
    -----------
    date : str
        date (ideally) in the format "%Y-%m-%d %H:%M:%S".

    """

    try:
        _ = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(
            "Invalid date format. Must be in '%Y-%m-%d %H:%M:%S' format, "
            "such as'2021-10-01 00:00:00'. Terminating script."
        )
        sys.exit()


def check_space_res(space_res: str) -> None:
    """Makes sure the space resolution haa a valid value.

    Parameters
    -----------
    space_res : str
        space resolution of the data. Must be either '4km' or '9km'.
    """
    if space_res not in ("4km", "9km"):
        print("Invalid 'space_res' value. Must be '4km' or '9km'. Terminating script.")
        sys.exit()


def check_time_res(time_res: str) -> None:
    """Makes sure the time resolution haa a valid value.

    Parameters
    -----------
    time_res : str
        time resolution of the data. Must be either 'YR', 'MO', '8D', or 'DAY'.
    """
    if time_res not in ("YR", "MO", "8D", "DAY"):
        print(
            "Invalid 'time_res' value. Must be either 'YR', 'MO', '8D', 'DAY'. "
            "Terminating script."
        )
        sys.exit()


def check_coords(subset_coords: tuple) -> None:
    """Makes sure the coordinates have valid format and values.

    Parameters
    -----------
    subset_coords : tuple
        subset coordinates in the format (lonmin, lonmax, latmin, latmax).
    """
    if (
        not (len(subset_coords) == 4)
        | (subset_coords[0] >= -180 & subset_coords[0] <= 180)
        | (subset_coords[1] >= -180 & subset_coords[1] <= 180)
        | (subset_coords[3] >= -90 & subset_coords[3] <= 90)
        | (subset_coords[2] >= -90 & subset_coords[2] <= 90)
    ):
        print(
            "Invalid 'subset coords' value. Must be (lonmin, lonmax, latmin, latmax), "
            "with negative signals if applicable. Terminating script."
        )
        sys.exit()


def find_nearest(array, target_value: int | float) -> (int, float):
    """Finds the index and value of an array element closest to a given target value.

    Parameters:
    -----------
    array : np.array or list
    target_value : int or float

    Returns:
    --------
    idx : index of the array element closest to the given target value
    array[idx] : value of the array element closest to the given target value.
    """

    array = np.asarray(array)
    idx = (
        np.abs(array - target_value)
    ).argmin()  # Returns the indices of the minimum values along an axis.
    return idx, array[idx]


def get_filelist_command(
    date_min: str,
    date_max: str,
    space_res: str,
    time_res: str,
    datadir: str = "../data",
) -> str:  #
    """
    Builds the command to get the list of files that correspond to the search.
    More info on https://oceandata.sci.gsfc.nasa.gov/api/file_search.

    Parameters:
    -----------
    date_min : str
        start date for data retrieval, in the format "%Y-%m-%d %H:%M:%S".
    date_max : str
        end date for data retrieval, in the format "%Y-%m-%d %H:%M:%S".
    space_res : str
        spatial resolution of the data. Must be either '4km' or '9km'.
    time_res : str
        temporal resolution of the data. Must be either 'YR', 'MO', '8D', 'DAY'.
    datadir : string
        directory where the list of data files will be created

    Returns:
        curl_command : string
    """
    url = (
        f"results_as_file=1&sensor_id=7&dtid=1043&sdate={date_min}&edate={date_max}"
        f"&subType=1&prod_id=chlor_a&resolution_id={space_res}&period={time_res}"
    )

    curl_command = (
        f"""curl -d "{url}" """
        f"""https://oceandata.sci.gsfc.nasa.gov/api/file_search > """
        f"""{datadir}/filelist.txt"""
    )

    return curl_command


def get_dates(filenames: list) -> (list, list, list, list, list, list):
    """Gets dates from each filename in order to build the opendap urls.

    Parameters
    -----------
    filenames : list


    Returns
    --------
    yeari : list
        year of the start date of the file
    monthi : list
        month of the start date of the file
    dayi : list
        day of the start date of the file
    yearf : list
        year of the end date of the file
    monthf : list
        month of the end date of the file
    dayf : list
        day of the end date of the file

    """

    dates_regex = re.compile("[0-9]{8}")

    yeari, yearf = [], []
    monthi, monthf = [], []
    dayi, dayf = [], []
    for filename in filenames:
        dates = re.findall(dates_regex, filename)
        yeari.append(dates[0][0:4]), yearf.append(dates[1][0:4])
        monthi.append(dates[0][4:6]), monthf.append(dates[1][4:6])
        dayi.append(dates[0][6:]), dayf.append(dates[1][6:])
        del dates
    del dates_regex
    return yeari, monthi, dayi, yearf, monthf, dayf


def get_dataset_keys(dataset_path: str) -> (str, str, str):
    """Gets the name of variables correspondent to longitude,
    latitude and chorophyll in a given dataset.

    Parameters
    -----------
    dataset_path : str
        opendap url of a dataset


    Returns
    --------
    lon_key : str
        name of the variable corresponding to longitude in the dataset
    lat_key : str
        name of the variable corresponding to latitude in the dataset
    chl_key : str
        name of the variable corresponding to chlorophyll in the dataset
    """
    # first gets dataset for the first time-step to do the subsetting
    # (opendap straight w/subsetting is not working)
    ds = nc.Dataset(dataset_path)
    var_dict = ds.variables

    # find the variable names (keys) correspondent to lon, lat and chl
    keys_dict = {"lon_key": [], "lat_key": [], "chl_key": []}
    for key in var_dict.keys():
        for word_part in ["lon", "lat", "chl"]:
            if word_part in key:
                keys_dict[f"{word_part}_key"] = key
                break

    # making sure all the keys were found
    for item in ["lon_key", "lat_key", "chl_key"]:
        if len(keys_dict[item]) == 0:
            print(
                f"key for {item} was not identified in required dataset. "
                f"Terminating script."
            )
            sys.exit()
        else:
            pass

    return keys_dict["lon_key"], keys_dict["lat_key"], keys_dict["chl_key"]
