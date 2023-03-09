# env packrat38
# useful links:
# main ones:
# https://oceandata.sci.gsfc.nasa.gov/api/file_search/
# https://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/L3SMI/
# secondary:
# https://www.earthdata.nasa.gov/
# https://search.earthdata.nasa.gov/search/granules/granule-details?p=C2330512018-OB_DAAC&pg[0][v]=f&pg[0][gsk]=-start_date&g=G2556030323-OB_DAAC&q=chlorophyll&polygon[0]=-27%2C-5.55717%2C-27%2C-17.36444%2C-11.25%2C-19.0512%2C-11.25%2C-2.74591%2C-21.9375%2C2.87661%2C-27%2C-5.55717&fi=MODIS&fdc=Ocean%2BBiology%2BDistributed%2BActive%2BArchive%2BCenter%2B%2528OB.DAAC%2529&tl=1673557731!3!!&lat=-0.28125&long=0.28125&zoom=0


# TO-DO: THE ISSUE W/ SERVER NOT WORKING MIGHT BE B/C AUTHENTICATION. CHECK THIS.
# BUT THESE ARE OPTIONS TO DOWNLOAD ALL THE FILES. i DON'T THINK i WANT TO DO THAT.
# https://stackoverflow.com/questions/33488179/how-do-i-download-pdf-file-over-https-with-python
# https://stackoverflow.com/questions/26745462/how-do-i-use-basic-http-authentication-with-the-python-requests-library

import time
import warnings
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import cm, ticker
from matplotlib.dates import DateFormatter

from src.utilities import (
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

# - plotting over time

title_datetime = datetime.fromisoformat(time_start[0].strip("Z"))
fig, ax = plt.subplots()

plt.ion()
for t in range(
    0, len(time_start)
):  # this should work even if there's just one time-step, since time_start is a list
    img = ax.contourf(
        lon,
        lat,
        chl[t, ...].squeeze(),
        vmin=0.0001,
        vmax=100,
        locator=ticker.LogLocator(),
        cmap=cm.viridis,
    )  # I think I need to set the limits here and that's it, no colorbar
    # plt.draw()
    # cbar = fig.colorbar(img, ax=ax)
    ax.set_title(f"Chlorophyll Concentration  -  {title_datetime.strftime('%b %Y')}")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    plt.show()
    time.sleep(1)
    # fig.clf(), fig.clf() # both not working
    ax.clear()  # removes the plot, but colorbar stays. works if I don't use colorbar.
    # cbar.remove() # this removes the colorbar but reduces the plotting area
    # plt.ion() # interactive mode on. maybe no need to use this if using pycharm
plt.close()
del fig

if len(time_start) > 1:
    # - plotting one frame to get the location for timeseries
    fig, ax = plt.subplots()
    aux = ax.contourf(
        lon,
        lat,
        chl[0, ...].squeeze(),
        vmin=0.0001,
        vmax=100,
        locator=ticker.LogLocator(),
        cmap=cm.viridis,
    )  # I think I need to set the limits here and that's it, no colorbar
    ax.set_title(
        f" Specify point for timeseries plot \n "
        f"Chlorophyll Concentration  {title_datetime.strftime('%b %Y')}"
    )
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    # plt.ion() # interactive mode on. no need to use this if using pycharm
    loc = plt.ginput(1, timeout=-1)[0]
    plt.close()
    del fig

    # - plotting timeseries
    loi, lov = find_nearest(lon, loc[0])
    lai, lav = find_nearest(lat, loc[1])

    # get+format dates for x-axis
    time_start_dt = [datetime.fromisoformat(t.strip("Z")) for t in time_start]
    formatter = DateFormatter("%Y-%m-%d")

    fig, ax = plt.subplots()
    # plt.plot_date(time_start_dt, chl[:, loc[1], loc[0]].squeeze())
    plt.plot_date(time_start_dt, chl[:, lai, loi].squeeze())
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 15]))
    ax.xaxis.set_major_formatter(formatter)
    ax.xaxis.set_tick_params(rotation=30, labelsize=0)
    ax.set_title(
        f"Chlorophyll Concentration @ lon = {lov:.1f}, lat = {lav:.1f}"
    )  # format floats python
    plt.show()
    time.sleep(1)
    # ax.set_xlabel("Time")
    # ax.set_ylabel("Chlorophyll concentration")
    # plt.ion() # interactive mode on
    del fig

    save_dataset(lon, lat, chl, time_start, time_end)

else:
    save_dataset(lon, lat, chl, time_start, time_end)

# TO-DO:
# eu deveria salvar a paleta de cores? como fazer isso?
# PUT IN A NOTEBOOK -- or not
# readme, license, folder tests, requirements.txt
