# env modisdatafetcher
# useful resources:
# primary:
# https://oceandata.sci.gsfc.nasa.gov/api/file_search/
# https://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/L3SMI/
# secondary:
# https://www.earthdata.nasa.gov/


from __future__ import annotations

import os
import sys
from datetime import date
import netCDF4 as nc
import numpy as np
import pprint

# from src.modisdatafetcher.utilities import (
#     check_date_format,
#     check_space_res,
#     check_time_res,
#     check_coords,
#     get_filelist_command,
#     get_dates,
#     find_nearest,
#     get_dataset_keys,
# )

from utilities import (
    check_date_format,
    check_space_res,
    check_time_res,
    check_coords,
    get_filelist_command,
    get_dates,
    find_nearest,
    get_dataset_keys,
)


def get_opendap_urls(
    date_min: str = "2021-11-01 00:00:00",
    date_max: str = "2022-01-01 00:00:00",
    space_res: str = "4km",  # "4km", "9km"
    time_res: str = "MO",  # YR, MO, 8D, DAY
    subset_coords: tuple = (-70, -25, -15, 20),
    datadir="../../data",
) -> list:
    """Builds urls for data access via opendap.

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
    subset_coords : tuple
        coordinates for data subset.
    datadir : str
        directory to save the data.

    Returns:
    --------
    dataset_urls : list
        list of urls for data access via opendap.
    """
    global dataset_urls, source, variable  # this here so save_dataset can have access to these variables

    opendap_base_url = "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/"
    level = "L3"
    map_bin = "m"
    source = "AQUA_MODIS"
    variable = "CHL"

    print("Requested data settings:\n")
    print(pprint.pprint(locals()))

    check_date_format(date_min)
    check_date_format(date_max)
    check_space_res(space_res)
    check_time_res(time_res)
    check_coords(subset_coords)

    # get & clean filenames list
    curl_command = get_filelist_command(
        date_min, date_max, space_res, time_res, datadir
    )
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


def get_subsetted_dataset(
    subset_coords: tuple, dataset_urls: list
) -> (list, list, list, list, list):
    """Subsets a dataset for the chosen geographical area, for multiple time-steps.

    Parameters
    -----------
    subset_coords : tuple
        coordinates for the subset in the format (lon_min, lon_max, lat_min, lat_max)
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
    # global subset_coords

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
    lon: np.ndarray,
    lat: np.ndarray,
    chl: np.ndarray,
    time_start: list,
    time_end: list,
    space_res: str = "4km",
    time_res: str = "MO",
    subset_coords: tuple = (-70, -25, -15, 20),
) -> None:
    """Saves the dataset in a netcdf file.

    Parameters
    -----------
    lon : array
    lat : array
    chl : array
    time_start : list
    time_end : list
    space_res : str
        space resolution of the data. Must be either '4km' or '9km'.
    time_res : str
        time resolution of the data. Must be either 'YR', 'MO', '8D', 'DAY'.
    subset_coords : tuple
        subset coordinates in the format (lonmin, lonmax, latmin, latmax).
    """
    # two options here: cftime and deal with it as string

    # get info for the filename of the dataset to be saved
    dataset = nc.Dataset(dataset_urls[0])
    lon_key, lat_key, chl_key = get_dataset_keys(dataset_urls[0])
    yeari, monthi, dayi, yearf, monthf, dayf = get_dates(dataset_urls)

    filename = (
        f"../../data/{source}_{variable}_{space_res}_{time_res}_"
        f"{yeari[0]}{monthi[0]}_{yearf[-1]}{monthf[-1]}_"
        f"{subset_coords[0]}_{subset_coords[1]}_"
        f"{subset_coords[2]}_{subset_coords[-1]}.nc"
    )
    print(f"## Filename under which the data will be saved: {filename} ##")

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
