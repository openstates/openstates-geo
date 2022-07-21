#!/usr/bin/env python3
import os
from io import BytesIO
import requests
import us
import zipfile

"""
note: The Census download URLs are case-sensitive
us has shapefiles as well, but they are out of date and don't have legislative data available
"""
YEAR = "2020"
URL = "https://www2.census.gov/geo/tiger/TIGER{year}/SLD{chamber_uppercase}/tl_{year}_{fips}_sld{chamber}.zip"


def download_and_extract(url, filename):
    response = requests.get(url, timeout=60)

    if response.status_code == 200:
        shapezip = BytesIO(response.content)
        with zipfile.ZipFile(shapezip) as f:
            f.extractall("./data/source")
    else:
        response.raise_for_status()


try:
    os.makedirs("./data/source/")
except FileExistsError:
    pass

for state in us.STATES + [us.states.PR, us.states.DC]:
    print("Fetching shapefiles for {}".format(state.name))

    for chamber in ["l", "u"]:
        fips = state.fips

        if state.abbr in ("DC", "NE") and chamber == "l":
            # skip lower chamber of the unicamerals
            continue

        if os.path.exists(f"data/source/tl_{YEAR}_{fips}_sld{chamber}.shp"):
            print(f"skipping {state} {fips} sld{chamber}")
            continue

        download_url = URL.format(
            fips=fips, chamber=chamber, chamber_uppercase=chamber.upper(), year=YEAR
        )

        filename = f"./data/tl_{YEAR}_{fips}_sld{chamber}.zip"
        download_and_extract(download_url, filename)

# final step: get US data
download_and_extract(
    f"https://www2.census.gov/geo/tiger/TIGER{YEAR}/CD/tl_{YEAR}_us_cd116.zip",
    f"data/source/tl_{YEAR}_us_cd116.zip",
)
