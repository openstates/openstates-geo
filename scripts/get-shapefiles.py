#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import zipfile
import requests
import shutil
import us

from shapefiles import SHAPEFILES


def clean_sources():
    """
    Nice function to clean up our source data
    if we're completely retrying
    """
    shutil.rmtree("./data/source")
    os.unlink("./data/*.zip")
    os.unlink("./data/*.mbtiles")
    shutil.rmtree("./data/geojson")
    shutil.rmtree("./data/mapbox")


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
        "--clean-sources",
        action="store_true",
        default=False,
        help="Remove any cached download/processed data",
    )
    args = parser.parse_args()

    if args.clean_sources:
        clean_sources()
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

        for chamber in ["lower", "upper", "congress"]:
            if jurisdiction.abbr in ("DC", "NE") and chamber == "lower":
                # skip lower chamber of the unicamerals
                continue


            if os.path.exists(f"data/source/tl_{YEAR}_{fips}_sld{chamber}.shp"):
                print(f"skipping {jurisdiction.name} {fips} sld{chamber}")
                continue

            filename = f"./data/tl_{YEAR}_{fips}_sld{chamber}.zip"
            download_and_extract(download_url, filename)
