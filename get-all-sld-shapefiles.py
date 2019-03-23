#! /usr/bin/env python3

# This could be done using Node instead, but that wouldn't let
# us remove the Python dependency, since `mapboxcli` is still
# needed and can only be installed as a Python package

import requests
import time
import us


# The Census download URLs are case-sensitive
URL = 'https://www2.census.gov/geo/tiger/TIGER2018/SLD{chamber_uppercase}/tl_2018_{fips}_sld{chamber}.zip'
MAX_ATTEMPTS = 3
SECONDS_BEFORE_RETRY = 5

for state in us.STATES + [us.states.PR]:
    print("Fetching shapefiles for {}".format(state.name))
    for chamber in ['l', 'u']:
        fips = state.fips
        download_url = URL.format(fips=fips, chamber=chamber, chamber_uppercase=chamber.upper())

        attempts = 0
        while attempts < MAX_ATTEMPTS:
            response = requests.get(download_url)
            if response.status_code not in [500, 503]:
                break
            else:
                attempts += 1
                time.sleep(SECONDS_BEFORE_RETRY)

        if response.status_code == 200:
            with open('./data/tl_2018_{fips}_sld{chamber}.zip'.format(fips=fips, chamber=chamber), 'wb') as f:
                f.write(response.content)
        elif (response.status_code == 404 and state.abbr == 'DC' and chamber == 'l') or \
                (response.status_code == 404 and state.abbr == 'NE' and chamber == 'l'):
            # These chambers are non-existant, and a `404` is expected
            pass
        else:
            # The Census seems to use `503` responses when overloaded
            response.raise_for_status()
