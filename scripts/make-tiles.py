#!/usr/bin/env python3
import subprocess
import glob
import os

if __name__ == "__main__":
    try:
        os.makedirs("./data/mapbox")
    except FileExistsError:
        pass

    print("Downloading national boundary")
    subprocess.run(
        "curl --silent --output ./data/source/cb_2017_us_nation_5m.zip https://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_us_nation_5m.zip".split()
    )
    subprocess.run(
        "unzip -q -o -d ./data/source ./data/source/cb_2017_us_nation_5m.zip".split()
    )

    print("Clip GeoJSON to shoreline")
    filenames = []
    for filename in sorted(glob.glob("data/geojson/*.geojson")):
        newfilename = filename.replace("/geojson/", "/mapbox/")
        filenames.append(newfilename)
        if os.path.exists(newfilename):
            print(f"{newfilename} exists, skipping")
        else:
            print(f"{filename} => {newfilename}")
            subprocess.run(
                [
                    "ogr2ogr",
                    "-clipsrc",
                    "./data/source/cb_2017_us_nation_5m.shp",
                    newfilename,
                    filename,
                ],
                check=True,
            )

    print("Combine to MBTiles file")
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
            "./sld.mbtiles",
        ]
        + filenames,
        check=True,
    )

    # if [ -z ${MAPBOX_ACCOUNT+x} ] || [ -z ${MAPBOX_ACCESS_TOKEN+x} ] ; then
    # 	echo "Skipping upload step; MAPBOX_ACCOUNT and/or MAPBOX_ACCESS_TOKEN not set in environment"
    # else
    # 	echo "Upload the MBTiles to Mapbox, for serving"
    # 	mapbox upload "${MAPBOX_ACCOUNT}.sld" ./sld.mbtiles
    # fi
