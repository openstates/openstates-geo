#!/usr/bin/env python3
import glob
import os
import requests
import subprocess
import urllib.request
import zipfile

YEAR = "2020"


def download_borders():
    """
    Download US borders and extract them
    """
    try:
        os.makedirs(f"{os.getcwd()}/data/mapbox")
    except FileExistsError:
        pass

    print("Downloading national boundary")
    """
    use urlretrieve instead of requests 'cause we can just
    define the output file easily
    """
    urllib.request.urlretrieve(
        f"https://www2.census.gov/geo/tiger/GENZ{YEAR}/shp/cb_{YEAR}_us_nation_5m.zip",
        f"data/source/cb_{YEAR}_us_nation_5m.zip",
    )

    with zipfile.ZipFile(
        f"{os.getcwd()}/data/source/cb_{YEAR}_us_nation_5m.zip", "r"
    ) as zf:
        zf.extractall(f"{os.getcwd()}/data/source/")


def create_mapbox_geojson():
    print("Clip GeoJSON to shoreline")
    sld_filenames = []
    cd_filenames = []
    for filename in sorted(glob.glob(f"{os.getcwd()}/data/geojson/*.geojson")):
        newfilename = filename.replace("/geojson/", "/mapbox/")
        if "sld" in newfilename:
            sld_filenames.append(newfilename)
        else:
            cd_filenames.append(newfilename)
        if os.path.exists(newfilename):
            print(f"{newfilename} exists, skipping")
        else:
            print(f"{filename} => {newfilename}")
            subprocess.run(
                [
                    "ogr2ogr",
                    "-clipsrc",
                    f"{os.getcwd()}/data/source/cb_{YEAR}_us_nation_5m.shp",
                    newfilename,
                    filename,
                ],
                check=True,
            )


def main():
    download_borders()
    create_mapbox_geojson()


if __name__ == "__main__":
    main()
