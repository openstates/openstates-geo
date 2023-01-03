#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import zipfile
import requests
import us

# note: The Census download URLs are case-sensitive
YEAR = "2022"
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


def find_jurisdiction(jur_name: str):
    for jur in us.STATES + [us.states.PR]:
        if jur_name == jur.name:
            return jur


if __name__ == "__main__":
    jur_names = [s.name for s in us.STATES + [us.states.PR]]
    parser = ArgumentParser(
        description="Download shapefiles for defined jurisdictions",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--jurisdiction",
        "-j",
        type=str,
        nargs="+",
        default=jur_names,
        help="The jurisdiction(s) to download shapefiles for",
    )
    parser.add_argument(
        "--get-us-data",
        action="store_true",
        default=False,
        help="Download US federal boundaries",
    )
    args = parser.parse_args()

    try:
        os.makedirs("./data/source/")
    except FileExistsError:
        pass

    for jur in args.jurisdiction:
        if jur not in jur_names:
            print(f"Invalid jurisdiction {jur}. Skipping.")
            continue
        jurisdiction = find_jurisdiction(jur)
        print(f"Fetching shapefiles for {jurisdiction.name}")

        for chamber in ["l", "u"]:
            fips = jurisdiction.fips

            if jurisdiction.abbr in ("DC", "NE") and chamber == "l":
                # skip lower chamber of the unicamerals
                continue

            if os.path.exists(f"data/source/tl_{YEAR}_{fips}_sld{chamber}.shp"):
                print(f"skipping {jurisdiction.name} {fips} sld{chamber}")
                continue

            download_url = URL.format(
                fips=fips, chamber=chamber, chamber_uppercase=chamber.upper(), year=YEAR
            )

            filename = f"./data/tl_{YEAR}_{fips}_sld{chamber}.zip"
            download_and_extract(download_url, filename)

    if args.get_us_data:
        print("Downloading US data")
        # final step: get US data
        download_and_extract(
            f"https://www2.census.gov/geo/tiger/TIGER{YEAR}/CD/tl_{YEAR}_us_cd116.zip",
            f"data/source/tl_{YEAR}_us_cd116.zip",
        )
