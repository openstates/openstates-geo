import glob
import os
import subprocess
from utils import ROOTDIR


def create_tiles(settings: dict):
    os.makedirs(f"{ROOTDIR}/data/mapbox", exist_ok=True)

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
            continue
        else:
            print(f"{filename} => {newfilename}")
            subprocess.run(
                [
                    "ogr2ogr",
                    "-clipsrc",
                    f"{ROOTDIR}/data/boundary/cb_{settings['BOUNDARY_YEAR']}_us_nation_5m.shp",
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
