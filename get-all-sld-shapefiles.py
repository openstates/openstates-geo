#!/usr/bin/env python3
import os
import zipfile
import requests
import us

# note: The Census download URLs are case-sensitive
YEAR = "2019"
URL = "https://www2.census.gov/geo/tiger/TIGER{year}/SLD{chamber_uppercase}/tl_{year}_{fips}_sld{chamber}.zip"

for state in us.STATES + [us.states.PR]:
    print("Fetching shapefiles for {}".format(state.name))

    for chamber in ["l", "u"]:
        fips = state.fips

        if os.path.exists(f"data/tl_{YEAR}_{fips}_sld{chamber}.shp"):
            print(f"skipping {state} {fips} sld{chamber}")
            continue

        download_url = URL.format(
            fips=fips, chamber=chamber, chamber_uppercase=chamber.upper(), year=YEAR
        )

        response = requests.get(download_url)

        if response.status_code == 200:
            filename = f"./data/tl_{YEAR}_{fips}_sld{chamber}.zip"

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
