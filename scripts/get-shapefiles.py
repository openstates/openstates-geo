#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import os
import zipfile
import requests
from utils import (
    JURISDICTION_NAMES,
    find_jurisdiction,
    ROOTDIR,
    TIGER_ROOT,
    setup_source,
    load_settings,
)


def download_from_tiger(jurisdiction, prefix):
    fips = jurisdiction.fips
    jur_name = jurisdiction.name.upper().replace(" ", "_")
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
            print(f"Skipping {jur}. No URLs configured.")
            continue
        print(f"Fetching shapefiles for {jur}")

        jurisdiction = find_jurisdiction(jur)
        download_from_tiger(jurisdiction, "RD18")
