# pytest test_get_chl3.py -v --durations=0
import os
from urllib.request import urlopen

import pytest

from src.modisdatafetcher.modisdatafetcher import get_opendap_urls
from src.modisdatafetcher.utilities import get_filelist_command


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


# temporary folder to store filelist.txt
@pytest.fixture(scope="function")
def tmpdir(tmp_path):
    tmp_dir = tmp_path
    return tmp_dir


# see if url to search for filenames is valid
def test_valid_file_search_url():
    file_search_url = "https://oceandata.sci.gsfc.nasa.gov/api/file_search"
    url_code = urlopen(file_search_url).getcode()
    assert url_code == 200


# get individual file names
def test_valid_get_filelist_command(settings_dict, tmpdir):
    curl_command = get_filelist_command(settings_dict, datadir=tmpdir)
    output = os.popen(curl_command).read()
    assert output != "No Results Found\n"


# check base url to go fetch the data
def test_valid_opendap_base_url(settings_dict):
    url = settings_dict["opendap_base_url"]
    url_code = urlopen(url).getcode()
    assert url_code == 200


# urls to go fetch individual data file
def test_get_opendap_urls(settings_dict, tmpdir):
    dataset_urls = get_opendap_urls(settings_dict, datadir=tmpdir)
    assert len(dataset_urls) == 2


# it would be nice to get new tests to check if the number of results is correct
