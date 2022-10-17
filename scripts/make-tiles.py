#!/usr/bin/env python3
import glob
import os
import subprocess
import urllib.request
import zipfile

if __name__ == "__main__":
    try:
        os.makedirs("./data/mapbox")
    except FileExistsError:
        pass

    print("Downloading national boundary")
    res = urllib.request.urlretrieve(
        "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_nation_5m.zip",
        "data/source/cb_2020_us_nation_5m.zip",
    )
    with zipfile.ZipFile("data/source/cb_2020_us_nation_5m.zip", "r") as zf:
        zf.extractall("data/source/")

    print("Clip GeoJSON to shoreline")
    sld_filenames = []
    cd_filenames = []
    for filename in sorted(glob.glob("data/geojson/*.geojson")):
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
                    "./data/source/cb_2020_us_nation_5m.shp",
                    newfilename,
                    filename,
                ],
                check=True,
            )

    # print("Combine to SLD MBTiles file")
    # subprocess.run(
    #     [
    #         "tippecanoe",
    #         "--layer",
    #         "sld",
    #         "--minimum-zoom",
    #         "2",
    #         "--maximum-zoom",
    #         "13",
    #         "--detect-shared-borders",
    #         "--simplification",
    #         "10",
    #         "--force",
    #         "--output",
    #         "./sld.mbtiles",
    #     ]
    #     + sld_filenames,
    #     check=True,
    # )

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
            "./cd.mbtiles",
        ]
        + cd_filenames,
        check=True,
    )

    # if [ -z ${MAPBOX_ACCOUNT+x} ] || [ -z ${MAPBOX_ACCESS_TOKEN+x} ] ; then
    # 	echo "Skipping upload step; MAPBOX_ACCOUNT and/or MAPBOX_ACCESS_TOKEN not set in environment"
    # else
    # 	echo "Upload the MBTiles to Mapbox, for serving"
    # 	mapbox upload "${MAPBOX_ACCOUNT}.sld" ./sld.mbtiles
    # fi
