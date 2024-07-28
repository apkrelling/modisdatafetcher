# env get_oceancolor
# useful resources:
# primary:
# https://oceandata.sci.gsfc.nasa.gov/api/file_search/
# https://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/L3SMI/
# secondary:
# https://www.earthdata.nasa.gov/


import time
import warnings
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import cm, ticker
from matplotlib.dates import DateFormatter

from utilities import (
    find_nearest,
    get_opendap_urls,
    get_subsetted_dataset,
    save_dataset,
)

warnings.filterwarnings(
    "ignore", message="Log scale: values of z <= 0 have been masked"
)

# BASIC SETTINGS
settings_dict = {
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

########################################################################################

dataset_urls = get_opendap_urls(settings_dict)

lon, lat, chl, time_start, time_end = get_subsetted_dataset(settings_dict, dataset_urls)

########################################################################################
########################################################################################

time_start_dt = [datetime.fromisoformat(t.strip("Z")) for t in time_start]
title_datetime = [t.strftime("%d %b %Y") for t in time_start_dt]
formatter = DateFormatter("%Y-%m-%d")

plt.ion()
fig, ax = plt.subplots()
for t in range(0, len(time_start)):
    img = ax.contourf(
        lon,
        lat,
        chl[t, ...].squeeze(),
        vmin=0.0001,
        vmax=100,
        locator=ticker.LogLocator(),
        cmap=cm.viridis,
    )
    if t == 0:
        cbar = fig.colorbar(img, ax=ax)
    ax.set_title(f"Chlorophyll Concentration  -  {title_datetime[t]}")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    plt.pause(2)
    ax.clear()
plt.close()
del fig

# it there's more than one time-step, plot chl timeseries at the designated location
if len(time_start) > 1:
    # - plot one frame to get the location for timeseries
    fig, ax = plt.subplots()
    aux = ax.contourf(
        lon,
        lat,
        chl[0, ...].squeeze(),
        vmin=0.0001,
        vmax=100,
        locator=ticker.LogLocator(),
        cmap=cm.viridis,
    )
    ax.set_title(
        f" Specify point for timeseries plot \n "
        f"Chlorophyll Concentration  {title_datetime[0]}"
    )
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    loc = plt.ginput(1, timeout=-1)[0]
    plt.close()
    del fig

    # plot timeseries
    loi, lov = find_nearest(lon, loc[0])
    lai, lav = find_nearest(lat, loc[1])

    fig, ax = plt.subplots()
    plt.plot_date(time_start_dt, chl[:, lai, loi].squeeze())
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 15]))
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_tick_params(rotation=20, labelsize=10)
    ax.set_title(f"Chlorophyll Concentration @ lon = {lov:.1f}, lat = {lav:.1f}")
    # plt.show()
    time.sleep(1)
    plt.close()
    del fig
    save_dataset(lon, lat, chl, time_start, time_end)
else:
    save_dataset(lon, lat, chl, time_start, time_end)
