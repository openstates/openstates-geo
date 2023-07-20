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

    cd_file = f"{ROOTDIR}/data/cd.mbtiles"
    if os.path.exists(cd_file):
        print(f"Existing CD tiles. Remove {cd_file} to re-generate")
    else:
        print("Generating CD MBTiles file")
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
    sld_file = f"{ROOTDIR}/data/sld.mbtiles"
    if os.path.exists(sld_file):
        print(f"Existing SLD tiles. Remove {sld_file} to re-generate")
    else:
        print("Generating SLD MBTiles file")
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


def _upload_tile(tileset: str, settings: dict, mapbox_token: str) -> None:
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
    print(f"Uploading {tileset} to Mapbox")
    s3.Object(bucket, key).put(Body=open(settings["path"], "rb").read())
    data = {"tileset": f"openstates.{tileset}", "url": url, "name": settings["name"]}
    resp = requests.post(
        f"https://api.mapbox.com/uploads/v1/{mapbox_user}", params=params, json=data
    ).json()
    upload_id = resp["id"]
    print(f"Starting processing of {tileset} ({settings['name']}) within Mapbox")
    resp = requests.get(
        f"https://api.mapbox.com/uploads/v1/{mapbox_user}/{upload_id}", params=params
    ).json()
    checks = 0
    while not resp["complete"]:
        time.sleep(10)
        checks += 1
        resp = requests.get(
            f"https://api.mapbox.com/uploads/v1/{mapbox_user}/{upload_id}",
            params=params,
        ).json()
        if resp["complete"]:
            break
        if checks and checks % 6 == 0:
            print(f"Still waiting on {tileset}")


def upload_tiles() -> None:
    """
    Following the pattern in https://docs.mapbox.com/api/maps/uploads/
    """
    mapbox_token = os.environ.get("MAPBOX_ACCESS_TOKEN")
    # tileset names are set for historical reasons
    tilesets = {
        "sld": {
            "path": f"{ROOTDIR}/data/sld.mbtiles",
            "name": "sld",
        },
        "cq8nw57b": {
            "path": f"{ROOTDIR}/data/cd.mbtiles",
            "name": "cd-diwr39",
        },
    }
    for tileset, settings in tilesets.items():
        _upload_tile(tileset, settings, mapbox_token)
