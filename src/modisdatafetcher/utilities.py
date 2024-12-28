from __future__ import annotations

import functools
import os
import re
import sys
from datetime import date, datetime

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


def check_date_format(item: str) -> bool:
    """Tests if input has "%Y-%m-%d %H:%M:%S" date format.

    Parameters:
    -----------
    item : str

    Returns:
    --------
    True if input has "%Y-%m-%d %H:%M:%S" date format, False if it doesn't.
    """

    try:
        _ = datetime.strptime(item, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


def check_settings(settings_dict: dict):
    """Makes sure the settings have valid parameters.

    This function checks all the items in settings_dict to make sure
    they are the values expected by the script. If any parameters in
    settings_dict are invalid, the script is terminated. If they are
    all valid, the script continues running.

    Parameters
    -----------
    settings_dict : dict
        info on the data to be retrieved

    """

    if not check_date_format(settings_dict["date_min"]):
        print(
            "Invalid 'date_min' value. Must be in '%Y-%m-%d %H:%M:%S' format, "
            "such as'2021-10-01 00:00:00'. Terminating script."
        )
        sys.exit()
    if not check_date_format(settings_dict["date_max"]):
        print(
            "Invalid 'date_max' value. Must be in '%Y-%m-%d %H:%M:%S' format, "
            "such as'2021-10-01 00:00:00'. Terminating script."
        )
        sys.exit()
    if not (
        (settings_dict["space_res"] == "4km") | (settings_dict["space_res"] == "9km")
    ):
        print("Invalid 'space_res' value. Must be '4km' or '9km'. Terminating script.")
        sys.exit()
    if (
        not (settings_dict["time_res"] == "YR")
        | (settings_dict["time_res"] == "MO")
        | (settings_dict["time_res"] == "8D")
        | (settings_dict["time_res"] == "DAY")
    ):
        print(
            "Invalid 'time_res' value. Must be either 'YR', 'MO', '8D', 'DAY'. "
            "Terminating script."
        )
        sys.exit()
    if not (
        settings_dict["opendap_base_url"]
        == "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/"
    ):
        print(
            "Invalid 'opendap_base_url' value. "
            "Must be 'http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/'. "
            "Terminating script."
        )
        sys.exit()
    if not (settings_dict["level"] == "L3"):
        print("Invalid 'level' value. Must be 'L3'. Terminating script.")
        sys.exit()
    if not (settings_dict["map_bin"] == "m"):
        print("Invalid 'map_bin' value. Must be 'm'. Terminating script.")
        sys.exit()
    if not (settings_dict["source"] == "AQUA_MODIS"):
        print("Invalid 'source' value. Must be 'AQUA_MODIS'. Terminating script.")
        sys.exit()
    if not (settings_dict["variable"] == "CHL"):
        print("Invalid 'variable' value. Must be 'CHL'. Terminating script.")
        sys.exit()
    if (
        not (len(settings_dict["subset_coords"]) == 4)
        | (
            settings_dict["subset_coords"][0]
            >= -180 & settings_dict["subset_coords"][0]
            <= 180
        )
        | (
            settings_dict["subset_coords"][1]
            >= -180 & settings_dict["subset_coords"][1]
            <= 180
        )
        | (
            settings_dict["subset_coords"][3]
            >= -90 & settings_dict["subset_coords"][3]
            <= 90
        )
        | (
            settings_dict["subset_coords"][2]
            >= -90 & settings_dict["subset_coords"][2]
            <= 90
        )
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


def get_filelist_command(settings_dict: dict, datadir="../data") -> str:  #
    """
    Builds the command to get the list of files that correspond to the search.
    More info on https://oceandata.sci.gsfc.nasa.gov/api/file_search.

    Parameters:
    -----------
    settings_dict : dict
        basic settings for the script to run
    datadir : string
        directory where the list of data files will be created

    Returns:
        curl_command : string
    """
    global space_res, time_res
    date_min = settings_dict["date_min"]
    date_max = settings_dict["date_max"]
    space_res = settings_dict["space_res"]
    time_res = settings_dict["time_res"]

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


def get_opendap_urls(settings_dict: dict, datadir="../../data") -> list:
    """Builds urls for data access via opendap.

    Parameters:
    -----------
    settings_dict : dict
        info on the data to be retrieved

    Returns:
    --------
    dataset_urls : list
        list of urls for data access via opendap.
    """

    global dataset_urls, source, variable

    check_settings(settings_dict)
    opendap_base_url = settings_dict["opendap_base_url"]
    level = settings_dict["level"]
    map_bin = settings_dict["map_bin"]
    source = settings_dict["source"]
    variable = settings_dict["variable"]

    # get & clean filenames list
    curl_command = get_filelist_command(settings_dict, datadir)
    os.system(curl_command)

    with open(f"{datadir}/filelist.txt", mode="r") as f:
        file_list = list(f)

    filenames = []
    for file in file_list:
        filenames.append(file.strip("\n"))
    del file_list

    # get dates for each file on the list in order to build opendap urls
    yeari, monthi, dayi, yearf, monthf, dayf = get_dates(filenames)

    # build opendap urls
    dataset_urls = []
    for k in range(len(yeari)):
        url = (
            f"{opendap_base_url}{level}SMI/{yeari[k]}/{monthi[k]}{dayi[k]}/"
            f"{source}.{yeari[k]}{monthi[k]}{dayi[k]}_{yearf[k]}{monthf[k]}{dayf[k]}."
            f"{level}{map_bin}.{time_res}.{variable}.chlor_a.{space_res}.nc"
        )
        dataset_urls.append(url)
    return dataset_urls


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


def get_subsetted_dataset(
    settings_dict: dict, dataset_urls: list
) -> (list, list, list, list, list):
    """Subsets a dataset for the chosen geographical area, for multiple time-steps.

    Parameters
    -----------
    settings_dict : dict
        info on the data to be retrieved
    dataset_urls : list
        list of urls for data access via opendap.


    Returns
    --------
    lon : np.array
    lat : np.array
    chl : np.array
    time_start : list
    time_end : list
    """
    global subset_coords
    subset_coords = settings_dict["subset_coords"]

    try:
        dataset = nc.Dataset(
            dataset_urls[0]
        )  # calls the nc dataset directly from the url
    except OSError:  # OSError: [Errno -70] NetCDF: DAP server error:
        print("## -- DAP server error: not able to reach files. Try again later. -- ##")
        sys.exit()

    lon_key, lat_key, chl_key = get_dataset_keys(dataset_urls[0])
    print(
        " \n ##### ----- Hang in there... this may take some time...  ----- ##### \n "
    )

    lon_original = dataset[lon_key][:]
    lat_original = dataset[lat_key][:]

    ilon = [
        find_nearest(lon_original, subset_coords[0])[0],
        find_nearest(lon_original, subset_coords[1])[0],
    ]
    ilat = [
        find_nearest(lat_original, subset_coords[2])[0],
        find_nearest(lat_original, subset_coords[3])[0],
    ]

    # doing this b/c lat and/or lon may not monotonically decrease
    ilon.sort()
    ilat.sort()

    # subsetting
    lon = lon_original[ilon[0] : ilon[1]]
    lat = lat_original[ilat[0] : ilat[1]]
    del lon_original, lat_original

    # in theory I should put the name of the dimension here
    # if var_dict[chl_key].dimensions[0] == 'lat':
    #     chl = dataset.variables[chl_key][ilat[0]:ilat[1], ilon[0]:ilon[1]]

    # Accumulate times and subsetted chl values here, for all dataset_urls
    time_start = []
    time_end = []
    for dataset_url in dataset_urls:
        print(
            f" Gathering info from file {dataset_url.split('/')[-1]} "
            f"- file {len(time_start) + 1}/{len(dataset_urls)} "
        )
        try:
            _dataset = nc.Dataset(dataset_url)
        except OSError:
            print(f"file {dataset_url.split('/')[-1]} is not reachable")
            continue

        time_start.append(
            _dataset.time_coverage_start
        )  # keeping as strings here b/c we can only save as str, int or float
        time_end.append(_dataset.time_coverage_end)
        _chl = _dataset.variables[chl_key][ilat[0] : ilat[1], ilon[0] : ilon[1]]
        if dataset_url == dataset_urls[0]:
            chl = _chl
        else:
            try:  # dataset_url == dataset_urls[1] (chl and _chl have the same shape)
                chl = np.stack((chl, _chl))
            except (
                ValueError
            ):  # (third or higher time-step / chl has one more dimension than _chl)
                chl = np.concatenate((chl, [_chl]), axis=0)
        _dataset.close()
        del _chl, _dataset
    del ilon, ilat

    return lon, lat, chl, time_start, time_end


def save_dataset(
    lon: np.ndarray, lat: np.ndarray, chl: np.ndarray, time_start: list, time_end: list
):
    """Saves the dataset in a netcdf file.

    Parameters
    -----------
    lon : array
    lat : array
    chl : array
    time_start : list
    time_end : list
    """
    # two options here: cftime and deal with it as string

    # get info for the filename of the dataset to be saved
    dataset = nc.Dataset(dataset_urls[0])
    lon_key, lat_key, chl_key = get_dataset_keys(dataset_urls[0])
    yeari, monthi, dayi, yearf, monthf, dayf = get_dates(dataset_urls)

    filename = (
        f"../data/{source}_{variable}_{space_res}_{time_res}_"
        f"{yeari[0]}{monthi[0]}_{yearf[-1]}{monthf[-1]}_"
        f"{subset_coords[0]}_{subset_coords[1]}_"
        f"{subset_coords[2]}_{subset_coords[-1]}.nc"
    )
    ds = nc.Dataset(filename, "w", format="NETCDF4")

    # -- assigning original and new global attrs -- ##
    attrs_list = dataset.ncattrs()

    # attributes that won't be copied from the original file
    remove_attrs = [
        "date_created",
        "time_coverage_start",
        "time_coverage_end",
        "start_orbit_number",
        "northernmost_latitude",
        "southernmost_latitude",
        "westernmost_longitude",
        "easternmost_longitude",
        "geospatial_lat_max",
        "geospatial_lat_min",
        "geospatial_lon_max",
        "geospatial_lon_min",
        "sw_point_latitude",
        "sw_point_longitude",
        "number_of_lines",
        "number_of_columns",
        "_lastModified",
        "data_minimum",
        "data_maximum",
    ]

    # taking out of the list the ones that will be modified
    for attr in remove_attrs:
        attrs_list.remove(attr)

    # assigning the ones that will the same as the original file
    for attr in attrs_list:
        ds.setncattr(attr, getattr(dataset, attr))

    # assigning the new ones
    ds.time_coverage_start = time_start[
        0
    ]  # .strftime("%d %B %Y") # time_coverage_start of the first file
    ds.time_coverage_end = time_end[
        -1
    ]  # .strftime("%d %B %Y") # time_coverage_end of the last file
    ds.northernmost_latitude = lat.max()
    ds.southernmost_latitude = lat.min()
    ds.westernmost_longitude = lon.max()
    ds.easternmost_longitude = lon.min()
    ds.geospatial_lat_max = lat.max()
    ds.geospatial_lat_min = lat.min()
    ds.geospatial_lon_max = lon.max()
    ds.geospatial_lon_min = lon.min()
    ds.sw_point_latitude = lat.min()
    ds.sw_point_longitude = lon.min()
    ds.number_of_lines = chl.shape[-2]
    ds.number_of_columns = chl.shape[-1]
    ds._lastModified = date.today().strftime("%d %B %Y")
    ds.data_minimum = chl.max()  # confirm this
    ds.data_maximum = (
        chl.min()
    )  # confirm this - -32767.0 -> aprender a lidar com esse valor aqui

    # -- creates dimensions -- ##
    #                            dimname, dimlength
    _ = ds.createDimension("nchars", 24)
    _ = ds.createDimension("time", len(time_start))
    _ = ds.createDimension("lat", len(lat))
    _ = ds.createDimension("lon", len(lon))

    # -- creates variables -- ##
    # times cannot be saves as datetime objects, only as np datatype object, or a str
    # that describes a np dtype object. Basically, can be  int, float, double, string.
    #                                   varname, vardtype, dims(tuple)
    time_start_var = ds.createVariable("time_start", "S1", ("time", "nchars"))
    time_end_var = ds.createVariable("time_end", "S1", ("time", "nchars"))
    lat_var = ds.createVariable("lat", "f4", ("lat",))  # _FillValue=-999.0)
    lon_var = ds.createVariable("lon", "f4", ("lon",))  # _FillValue=-999.0)
    chl_var = ds.createVariable(
        "chl",
        "f4",
        (
            "time",
            "lat",
            "lon",
        ),
        fill_value=-32767.0,
    )

    # -- assigns values to variables -- ##
    t_start = np.array(time_start, dtype="S24")
    time_start_var._Encoding = "ascii"  # this enables automatic conversion
    time_start_var[:] = t_start

    t_end = np.array(time_start, dtype="S24")
    time_end_var._Encoding = "ascii"  # this enables automatic conversion
    time_end_var[:] = t_end

    lat_var[:] = lat
    lon_var[:] = lon
    chl_var[:] = chl

    # -- assigning variables attrs - those will all be maintained -- ##
    chl_attrs = dataset.variables[chl_key].ncattrs()
    chl_attrs.remove("_FillValue")
    for attr in chl_attrs:
        ds.variables["chl"].setncattr(attr, getattr(dataset.variables[chl_key], attr))

    lat_attrs = dataset.variables[lat_key].ncattrs()
    lat_attrs.remove("_FillValue")
    for attr in lat_attrs:
        ds.variables["lat"].setncattr(attr, getattr(dataset.variables[lat_key], attr))

    lon_attrs = dataset.variables[lon_key].ncattrs()
    lon_attrs.remove("_FillValue")
    for attr in lon_attrs:
        ds.variables["lon"].setncattr(attr, getattr(dataset.variables[lon_key], attr))

    ds.close()
    print(f"## -- File {filename} saved! -- ##")
