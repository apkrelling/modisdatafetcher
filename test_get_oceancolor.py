# pytest test_get_chl3.py -v --durations=0
import os
from urllib.request import urlopen

import pytest

from utilities import get_filelist_command, get_opendap_urls


@pytest.fixture
def settings_dict():
    return {
        "date_min": "2021-11-01 00:00:00",
        "date_max": "2022-01-01 00:00:00",
        "space_res": "4km",  # "4km", "9km"
        "time_res": "MO",  # YR, MO, 8D, DAY
        "opendap_base_url": "http://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/",
        "level": "L3",
        "map_bin": "m",
        "source": "AQUA_MODIS",
        "variable": "CHL",
        "subset_coords": (-70, -25, -15, 20),
    }


def test_valid_file_search_url():
    file_search_url = "https://oceandata.sci.gsfc.nasa.gov/api/file_search"
    url_code = urlopen(file_search_url).getcode()
    assert url_code == 200


def test_valid_get_filelist_command(settings_dict):
    curl_command = get_filelist_command(settings_dict)
    output = os.popen(curl_command).read()
    assert output != "No Results Found\n"


def test_valid_opendap_base_url(settings_dict):
    url = settings_dict["opendap_base_url"]
    url_code = urlopen(url).getcode()
    assert url_code == 200


def test_get_opendap_urls(settings_dict):
    dataset_urls = get_opendap_urls(settings_dict)
    assert len(dataset_urls) == 2


@pytest.mark.skip("no way of currently testing this")
def test_any_files_in_filelist():
    with open("data/filelist.txt", mode="r") as f:
        file_list = list(f)
    assert len(file_list) > 0
