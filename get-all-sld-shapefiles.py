#! /usr/bin/env python3

import logging
import time
import zipfile

import requests
import us


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# The Census download URLs are case-sensitive
YEAR = "2019"
URL = "https://www2.census.gov/geo/tiger/TIGER{year}/SLD{chamber_uppercase}/tl_{year}_{fips}_sld{chamber}.zip"
MAX_ATTEMPTS = 3
SECONDS_BEFORE_RETRY = 5

for state in us.STATES + [us.states.PR]:
    logger.info("Fetching shapefiles for {}".format(state.name))

    for chamber in ["l", "u"]:
        fips = state.fips
        download_url = URL.format(
            fips=fips, chamber=chamber, chamber_uppercase=chamber.upper(), year=YEAR
        )

        attempts = 0
        while attempts < MAX_ATTEMPTS:
            response = requests.get(download_url)
            if response.status_code not in [500, 503]:
                break
            else:
                attempts += 1
                time.sleep(SECONDS_BEFORE_RETRY)

        if response.status_code == 200:
            filename = "./data/tl_2018_{fips}_sld{chamber}.zip".format(
                fips=fips, chamber=chamber
            )
            # This _could_ all be done with a single file operation,
            # by using a `BytesIO` file-like object to temporarily hold the
            # HTTP response. However, that's less readable and maintainable,
            # and a bit of delay isn't a problem given the slowness
            # of the Census downloads in the first place.
            with open(filename, "wb") as f:
                f.write(response.content)
            with zipfile.ZipFile(filename, "r") as f:
                f.extractall("./data")
        elif (
            response.status_code == 404 and state.abbr == "DC" and chamber == "l"
        ) or (response.status_code == 404 and state.abbr == "NE" and chamber == "l"):
            # These chambers are non-existant, and a `404` is expected
            pass
        else:
            response.raise_for_status()
