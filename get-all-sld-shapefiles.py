#! /usr/bin/env python3

# This could be done using Node instead, but that wouldn't let
# us remove the Python dependency, since `mapboxcli` is still
# needed and can only be installed as a Python package

import requests
import time
import us


# The Census download URLs are case-sensitive
URL = 'https://www2.census.gov/geo/tiger/TIGER2018/SLD{chamber_uppercase}/tl_2018_{fips}_sld{chamber}.zip'
SECONDS_DELAY_TO_AVOID_RATE_LIMITING = 3

for state in us.STATES + [us.states.PR]:
    print("Fetching shapefiles for {}".format(state.name))
    for chamber in ['l', 'u']:
        time.sleep(SECONDS_DELAY_TO_AVOID_RATE_LIMITING)
        fips = state.fips
        download_url = URL.format(fips=fips, chamber=chamber, chamber_uppercase=chamber.upper())
        data = requests.get(download_url).content
        with open('./data/tl_2018_{fips}_sld{chamber}.zip'.format(fips=fips, chamber=chamber), 'wb') as f:
            f.write(data)
