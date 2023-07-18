import boto3
from datetime import datetime
import geopandas as gpd
import glob
import json
import os

from .general import ROOTDIR


def _make_boundaries():
    os.makedirs(f"{ROOTDIR}/data/boundaries", exist_ok=True)
    year = datetime.now().date().year
    for file in glob.glob(f"{ROOTDIR}/data/geojson/*.geojson"):
        with open(file, "r") as f:
            obj = json.load(f)
        print(f"Processing {file} into district-level boundary files")
        for feature in obj["features"]:
            # skip empty features
            if "ocdid" not in feature["properties"]:
                continue
            subpath = feature["properties"]["ocdid"]
            full_path = f"{ROOTDIR}/data/boundaries/{subpath}.json"
            if os.path.exists(full_path):
                continue
            folder = "/".join(subpath.split("/")[:-1])
            os.makedirs(f"{ROOTDIR}/data/boundaries/{folder}", exist_ok=True)
            gdf = gpd.GeoDataFrame.from_features([feature])
            bounds = gdf["geometry"].bounds
            centroid = gdf["geometry"].centroid
            obj = {
                "shape": feature["geometry"],
                "metadata": feature["properties"],
                "division_id": feature["properties"]["ocdid"],
                "year": year,
                "extent": [
                    bounds.minx[0],
                    bounds.miny[0],
                    bounds.maxx[0],
                    bounds.maxy[0],
                ],
                "centroid": {
                    "coordinates": [
                        centroid.x[0],
                        centroid.y[0],
                    ],
                    "type": "Point",
                },
            }
            with open(full_path, "w") as f:
                json.dump(obj, f)


def bulk_upload(settings: dict):
    _make_boundaries()

    # all geojson files processed...now to upload
    print("Uploading division files to S3")
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=settings["aws_user"],
        aws_secret_access_key=settings["aws_password"],
    )
    bucket = settings["bucket"]
    prefix_path = f"{ROOTDIR}/data/boundaries"
    bucket_path = f"boundaries/{year}"
    for index, file in enumerate(glob.glob(f"{prefix_path}/**/*.json", recursive=True)):
        path = file.removeprefix(f"{prefix_path}/")
        path = f"{bucket_path}/{path}"
        s3.Object(bucket, path).put(Body=open(file, "r").read(), ACL="public-read")
        if index and index % 50 == 0:
            print(f"Processed {index} files...")
