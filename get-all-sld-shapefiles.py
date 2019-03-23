#! /usr/bin/env python3

# This could be done using Node instead, but that wouldn't let
# us remove the Python dependency, since `mapboxcli` is still
# needed and can only be installed as a Python package

import requests
import time
import us


# The Census download URLs are case-sensitive
URL = 'https://www2.census.gov/geo/tiger/TIGER2018/SLD{chamber_uppercase}/tl_2018_{fips}_sld{chamber}.zip'
SECONDS_DELAY_TO_AVOID_RATE_LIMITING = 1

for state in us.STATES + [us.states.PR]:
    print("Fetching shapefiles for {}".format(state.name))
    for chamber in ['l', 'u']:
        time.sleep(SECONDS_DELAY_TO_AVOID_RATE_LIMITING)

        fips = state.fips
        download_url = URL.format(fips=fips, chamber=chamber, chamber_uppercase=chamber.upper())
        response = requests.get(download_url)

        if response.status_code == 200:
            with open('./data/tl_2018_{fips}_sld{chamber}.zip'.format(fips=fips, chamber=chamber), 'wb') as f:
                f.write(response.content)
        elif (state.abbr == 'DC' and chamber == 'l') or \
                (state.abbr == 'NE' and chamber == 'l'):
            # These chambers are non-existant, and a `404` is expected
            pass
        else:
            response.raise_for_status()
