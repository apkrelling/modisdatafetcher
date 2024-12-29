# pytest test_get_chl3.py -v --durations=0

import pytest
from src.modisdatafetcher.modisdatafetcher import (
    get_opendap_urls,
    get_subsetted_dataset,
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


def test_get_opendap_urls(settings_dict, tmpdir):
    dataset_urls = get_opendap_urls(
        settings_dict["date_min"],
        settings_dict["date_max"],
        settings_dict["space_res"],
        settings_dict["time_res"],
        settings_dict["subset_coords"],
        datadir=tmpdir,
    )
    assert len(dataset_urls) == 2


def test_get_subsetted_dataset(settings_dict):
    lon, lat, chl, time_start, time_end = get_subsetted_dataset(
        subset_coords=settings_dict["subset_coords"],
        dataset_urls=settings_dict["dataset_urls"],
    )
    assert len(lon)
