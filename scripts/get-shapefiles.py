#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import os
import zipfile
import requests
import shutil
import us
import yaml


def load_settings(config_file: str):
    with open(config_file, "r") as f_in:
        settings = yaml.safe_load(f_in.read())
    return settings


def clean_sources():
    """
    simple function to clean up our source data
    if we're completely retrying
    """
    cwd = os.getcwd()
    shutil.rmtree(f"{cwd}/data/source", ignore_errors=True)
    os.makedirs(f"{os.getcwd()}/data/source/")
    for f in glob.glob(f"{cwd}/data/*.zip"):
        os.unlink(f)
    for f in glob.glob(f"{cwd}/data/*.mbtiles"):
        os.unlink(f)
    shutil.rmtree(f"{cwd}/data/geojson", ignore_errors=True)
    os.makedirs(f"{os.getcwd()}/data/geojson/")


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
            f.extractall(f"{os.getcwd()}/data/source")
    else:
        response.raise_for_status()


if __name__ == "__main__":
    jur_names = [s.name for s in us.STATES + [us.states.PR, us.states.DC]]
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
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=f"{os.getcwd()}/scripts/settings.yml",
        help="Config file for downloading geo data",
    )
    args = parser.parse_args()

    if args.clean_sources:
        clean_sources()
    SETTINGS = load_settings(args.config)

    for jur in args.jurisdiction:
        if jur not in jur_names:
            print(f"Invalid jurisdiction {jur}. Skipping.")
            continue
        if jur not in SETTINGS["shapefile_urls"]:
            print(f"Skipping {jur}. No URLs configured.")
            continue
        print(f"Fetching shapefiles for {jur}")

        for chamber, url in SETTINGS["shapefile_urls"][jur].items():
            filename = f"{os.getcwd()}/data/{url.rsplit('/' , 1)[1]}"

            if os.path.exists(f"{os.getcwd()}/data/{filename}"):
                print(f"skipping {jur} {chamber}")
                continue

            download_and_extract(url, filename)
