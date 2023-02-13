#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import os
import zipfile
import requests
import urllib.request

from utils import (
    JURISDICTION_NAMES,
    find_jurisdiction,
    ROOTDIR,
    TIGER_ROOT,
    setup_source,
    load_settings,
)


def download_from_tiger(jurisdiction, prefix, settings):
    """
    URLs are somewhat hard-coded here...
    Generally...download three files for each jurisdiction:
    1. Federal congress (cd) boundaries
    2. Upper chamber boundaries (sldu)
    3. lower chamber boundaries (sldl)
    Some jurisdictions (e.g. NE, DC) don't have all three files
    so we allow a download to fail and just log and move on
    """
    fips = jurisdiction.fips
    jur_name = settings["FIPS_NAME_MAP"].get(
        fips, jurisdiction.name.upper().replace(" ", "_")
    )
    url_root = f"{TIGER_ROOT}/TIGER_{prefix}/STATE/{fips}_{jur_name}/{fips}"
    urls = (
        f"{url_root}/tl_rd22_{fips}_cd118.zip",
        f"{url_root}/tl_rd22_{fips}_sldu.zip",
        f"{url_root}/tl_rd22_{fips}_sldl.zip",
    )
    for url in urls:
        chamber = url.split("/")[-1]
        fullpath = f"{ROOTDIR}/data/{chamber}"
        if os.path.exists(fullpath):
            print(f"skipping {jurisdiction.name} {chamber}")
            continue
        try:
            _download_and_extract(url, fullpath)
        except Exception as e:
            print(f"Couldn't download {jurisdiction.name} {chamber} :: {e}")


def download_boundary_file(boundary_year: str):
    """
    Use separate download pattern because this file
    needs to be processed separately
    """
    output = f"{ROOTDIR}/data/cb_{boundary_year}_us_nation_5m.zip"
    if os.path.exists(output):
        print("Boundary file exists. Skipping download.")
        return
    url = f"{TIGER_ROOT}/GENZ{boundary_year}/shp/cb_{boundary_year}_us_nation_5m.zip"
    print(f"Downloading national boundary from {url}")
    _ = urllib.request.urlretrieve(url, output)
    with zipfile.ZipFile(output, "r") as zf:
        zf.extractall(f"{ROOTDIR}/data/boundary/")


def _download_and_extract(url: str, filename: str):
    response = requests.get(url)

    if response.status_code == 200:
        # This _could_ all be done with a single file operation,
        # by using a `BytesIO` file-like object to temporarily hold the
        # HTTP response. However, that's less readable and maintainable,
        # and a bit of delay isn't a problem given the slowness
        # of the Census downloads in the first place.
        with open(filename, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(filename, "r") as z:
            for obj in z.infolist():
                try:
                    z.extract(obj, f"{ROOTDIR}/data/source_cache/")
                except Exception as e:
                    print(f"Failed to extract {obj.filename}: {e}")
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
        default=JURISDICTION_NAMES,
        help="The jurisdiction(s) to download shapefiles for",
    )
    parser.add_argument(
        "--clean-source",
        action="store_true",
        default=False,
        help="Remove any cached download/processed data",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=f"{ROOTDIR}/configs",
        help="Config directory for downloading geo data",
    )
    args = parser.parse_args()

    setup_source(args.clean_source)
    SETTINGS = load_settings(args.config)

    for jur in args.jurisdiction:
        if jur not in JURISDICTION_NAMES:
            print(f"Invalid jurisdiction {jur}. Skipping.")
            continue
        if jur not in SETTINGS["jurisdictions"]:
            print(f"Skipping {jur}. No configuration present.")
            continue
        print(f"Fetching shapefiles for {jur}")

        jurisdiction = find_jurisdiction(jur)
        download_from_tiger(jurisdiction, "RD18", SETTINGS)
    download_boundary_file(SETTINGS["BOUNDARY_YEAR"])
