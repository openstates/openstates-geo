import boto3
import glob
import os
import requests
import subprocess
import time

from .general import ROOTDIR


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


def _upload_tile(tileset: str, filepath: str, mapbox_token: str) -> None:
    """
    Actually upload a tileset to mapbox
    """
    mapbox_user = "openstates"
    params = {"access_token": mapbox_token}
    resp = requests.post(
        f"https://api.mapbox.com/uploads/v1/{mapbox_user}/credentials", params=params
    ).json()
    bucket = resp["bucket"]
    key = resp["key"]
    access_id = resp["accessKeyId"]
    access_key = resp["secretAccessKey"]
    session_token = resp["sessionToken"]
    url = resp["url"]
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=access_id,
        aws_secret_access_key=access_key,
        aws_session_token=session_token,
    )
    s3.Object(bucket, key).put(Body=open(filepath, "r").read())

    data = {"tileset": f"openstates.{tileset}", "url": url}
    resp = requests.post(
        f"https://api.mapbox.com/uploads/v1/{mapbox_user}", params=params, json=data
    ).json()
    upload_id = resp["id"]
    resp = requests.get(
        f"https://api.mapbox.com/uploads/v1/{mapbox_user}/{upload_id}", params=params
    ).json()
    while not resp["complete"]:
        time.sleep(10)
        resp = requests.get(
            f"https://api.mapbox.com/uploads/v1/{mapbox_user}/{upload_id}",
            params=params,
        ).json()


def upload_tiles() -> None:
    """
    Following the pattern in https://docs.mapbox.com/api/maps/uploads/
    """
    mapbox_token = os.environ.get("MAPBOX_ACCESS_TOKEN")
    tilesets = {
        "sld": f"{ROOTDIR}/data/sld.mbtiles",
        "cd-diwr39": f"{ROOTDIR}/data/cd.mbtiles",
    }
    for tileset, filename in tilesets.items():
        _upload_tile(tileset, filename, mapbox_token)
