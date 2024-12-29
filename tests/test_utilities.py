import os
from urllib.request import urlopen

import pytest

import numpy as np
from src.modisdatafetcher.utilities import (
    check_date_format,
    check_space_res,
    check_time_res,
    check_coords,
    find_nearest,
    get_filelist_command,
    get_dates,
    get_dataset_keys,
)


@pytest.fixture
def settings_dict():
    return {
        "date_min": "2021-11-01 00:00:00",
        "date_max": "2022-01-01 00:00:00",
        "space_res": "4km",
        "time_res": "MO",
        "opendap_base_url": "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/",
        "level": "L3",
        "map_bin": "m",
        "source": "AQUA_MODIS",
        "variable": "CHL",
        "subset_coords": (-70, -68, -15, -13),
        "dataset_path": "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/L3SMI/2021/1101/AQUA_MODIS.20211101_20211130.L3m.MO.CHL.chlor_a.4km.nc",
        "filename": ["AQUA_MODIS.20211101_20211130.L3m.MO.CHL.chlor_a.4km.nc"],
        "dataset_urls": [
            "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/L3SMI/2021/1101/AQUA_MODIS.20211101_20211130.L3m.MO.CHL.chlor_a.4km.nc"
        ],
    }


# temporary folder to store filelist.txt
@pytest.fixture(scope="function")
def tmpdir(tmp_path):
    tmp_dir = tmp_path
    return tmp_dir


# check if base url to go fetch the data is active
def test_valid_opendap_base_url(settings_dict):
    url = settings_dict["opendap_base_url"]
    url_code = urlopen(url).getcode()
    assert url_code == 200


def test_check_date_format(settings_dict):
    check_date_format(settings_dict["date_min"])


def test_check_space_res(settings_dict):
    check_space_res(settings_dict["space_res"])


def test_check_time_res(settings_dict):
    check_time_res(settings_dict["time_res"])


def test_check_coords(settings_dict):
    check_coords(settings_dict["subset_coords"])


def test_find_nearest():
    assert find_nearest(np.array([2, 3, 3.1, 4]), 3.5) == (2, 3.1)


def test_valid_get_filelist_command(settings_dict, tmpdir):
    curl_command = get_filelist_command(
        settings_dict["date_min"],
        settings_dict["date_max"],
        settings_dict["space_res"],
        settings_dict["time_res"],
        datadir=tmpdir,
    )
    output = os.popen(curl_command).read()
    assert output != "No Results Found\n"


def test_get_dates(settings_dict):
    yi, mi, di, yf, mf, df = get_dates(settings_dict["filename"])
    assert (yi, mi, di, yf, mf, df) == (
        ["2021"],
        ["11"],
        ["01"],
        ["2021"],
        ["11"],
        ["30"],
    )


def test_get_dataset_keys(settings_dict):
    coor1, coor2, var = get_dataset_keys(settings_dict["dataset_path"])
    assert (coor1, coor2, var) == ("lon", "lat", "chlor_a")
