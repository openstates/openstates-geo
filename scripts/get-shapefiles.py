#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import os
import zipfile
import requests
import shutil
import us
import yaml

jur_names = [s.name for s in us.STATES + [us.states.PR, us.states.DC]]
cwd = os.getcwd()


def load_settings(config_file: str):
    with open(config_file, "r") as f_in:
        settings = yaml.safe_load(f_in.read())
    return settings


def find_jurisdiction(jur_name: str):
    """
    Return a github.com/unitedstates/python-us style
    jurisdiction object so we can (potentially) back fill
    """
    for jurisdiction in [s for s in us.STATES + [us.states.PR, us.states.DC]]:
        if jur_name == jurisdiction.name:
            return jurisdiction


def clean_sources():
    """
    simple function to clean up our source data
    if we're completely retrying
    """
    shutil.rmtree(f"{cwd}/data/source", ignore_errors=True)
    os.makedirs(f"{cwd}/data/source/")
    for f in glob.glob(f"{cwd}/data/*.zip"):
        os.unlink(f)
    for f in glob.glob(f"{cwd}/data/*.mbtiles"):
        os.unlink(f)
    shutil.rmtree(f"{cwd}/data/geojson", ignore_errors=True)
    os.makedirs(f"{cwd}/data/geojson/")


def download_from_tiger(jurisdiction, year):
    fips = jurisdiction.fips
    for chamber in ["u", "l"]:
        url = f"https://www2.census.gov/geo/tiger/TIGER{year}/SLD{chamber.upper()}/tl_{year}_{fips}_sld{chamber}.zip"
        filename = f"{cwd}/data/tl_{year}_{fips}_sld{chamber}.zip"
        if os.path.exists(filename):
            print(f"{filename} already downloaded...skipping")
            continue
        try:
            _download_and_extract(url, filename)
        except Exception as e:
            print(f"Couldn't download {jurisdiction.name} {chamber} :: {e}")


def download_from_arp(jur_urls: dict):
    for chamber, url in jur_urls.items():
        filename = f"{cwd}/data/{url.rsplit('/' , 1)[1]}"

        if os.path.exists(filename):
            print(f"skipping {jur} {chamber}")
            continue

        _download_and_extract(url, filename)


def _download_and_extract(url, filename):
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
            f.extractall(f"{cwd}/data/source")
    else:
        response.raise_for_status()


if __name__ == "__main__":
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
        default=f"{cwd}/scripts/settings.yml",
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

        if SETTINGS["shapefile_urls"][jur].get("use_tiger", False):
            jurisdiction = find_jurisdiction(jur)
            download_from_tiger(jurisdiction, SETTINGS["YEAR"])
        else:
            download_from_arp(SETTINGS["shapefile_urls"][jur])

    us_source = f"{cwd}/data/tl_{SETTINGS['YEAR']}_us_cd116.zip"
    if not os.path.exists(us_source):
        _download_and_extract(
            f"https://www2.census.gov/geo/tiger/TIGER{SETTINGS['YEAR']}/CD/tl_{SETTINGS['YEAR']}_us_cd116.zip",
            us_source,
        )
