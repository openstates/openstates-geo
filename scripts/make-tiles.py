#!/usr/bin/env python3
import glob
import os
import subprocess
import urllib.request
import zipfile
from utils import ROOTDIR

YEAR = "2021"


if __name__ == "__main__":
    try:
        os.makedirs(f"{ROOTDIR}/data/mapbox")
        os.makedirs(f"{ROOTDIR}/data/boundary")
    except FileExistsError:
        pass

    print("Downloading national boundary")
    res = urllib.request.urlretrieve(
        f"https://www2.census.gov/geo/tiger/GENZ{YEAR}/shp/cb_{YEAR}_us_nation_5m.zip",
        f"{ROOTDIR}/data/cb_{YEAR}_us_nation_5m.zip",
    )
    with zipfile.ZipFile(f"{ROOTDIR}/data/cb_{YEAR}_us_nation_5m.zip", "r") as zf:
        zf.extractall(f"{ROOTDIR}/data/boundary/")

    print("Clip GeoJSON to shoreline")
    sld_filenames = []
    cd_filenames = []
    for filename in sorted(glob.glob(f"{ROOTDIR}/data/geojson/*.geojson")):
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
                    f"{ROOTDIR}/data/boundary/cb_{YEAR}_us_nation_5m.shp",
                    newfilename,
                    filename,
                ],
                check=True,
            )

    print("Combine to CD MBTiles file")
    subprocess.run(
        [
            "tippecanoe",
            "--layer",
            "cd",
            "--minimum-zoom",
            "2",
            "--maximum-zoom",
            "13",
            "--detect-shared-borders",
            "--simplification",
            "10",
            "--force",
            "--output",
            f"{ROOTDIR}/data/cd.mbtiles",
        ]
        + cd_filenames,
        check=True,
    )

    print("Combine to SLD MBTiles file")
    subprocess.run(
        [
            "tippecanoe",
            "--layer",
            "sld",
            "--minimum-zoom",
            "2",
            "--maximum-zoom",
            "13",
            "--detect-shared-borders",
            "--simplification",
            "10",
            "--force",
            "--output",
            f"{ROOTDIR}/data/sld.mbtiles",
        ]
        + sld_filenames,
        check=True,
    )
    mb_account = os.environ.get("MAPBOX_ACCOUNT", None)
    mb_token = os.environ.get("MAPBOX_ACCESS_TOKEN", None)
    if mb_account and mb_token:
        print("Upload to Mapbox")
        subprocess.run(
            [
                "poetry",
                "run",
                "mapbox",
                "upload",
                f"{mb_account}.sld",
                f"{ROOTDIR}/data/sld.mbtiles",
            ],
            check=True,
        )
    else:
        print("Skipping upload to Mapbox...environment variables missing")
