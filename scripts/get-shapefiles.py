#!/usr/bin/env python3
import os
import glob
import zipfile
import requests
import us

# note: The Census download URLs are case-sensitive
YEAR = "2020"
URL = "https://www2.census.gov/geo/tiger/TIGER{year}/SLD{chamber_uppercase}/tl_{year}_{fips}_sld{chamber}.zip"


def download_and_extract(url, filename):
    response = requests.get(url)

    if response.status_code == 200:
        # This _could_ all be done with a single file operation,
        # by using a `BytesIO` file-like object to temporarily hold the
        # HTTP response. However, that's less readable and maintainable,
        # and a bit of delay isn't a problem given the slowness
        # of the Census downloads in the first place.
        with open(filename, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(filename, "r") as f:
            f.extractall("./data/source")
    else:
        response.raise_for_status()


try:
    os.makedirs("./data/source/")
except FileExistsError:
    pass

for state in us.STATES + [us.states.PR]:
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
