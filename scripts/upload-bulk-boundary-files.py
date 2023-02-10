#!/usr/bin/env python3

from datetime import datetime
import geopandas as gpd
import glob
import json
import os
import boto3

from utils import ROOTDIR


def main():
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
            folder = feature["properties"]["ocdid"]
            filename = f"{feature['properties']['type']}:.json"
            full_path = f"{ROOTDIR}/data/boundaries/{folder}/{filename}.json"
            if os.path.exists(full_path):
                continue
            os.makedirs(f"{ROOTDIR}/data/boundaries/{folder}", exist_ok=True)
            gdf = gpd.GeoDataFrame.from_features([feature])
            obj = {
                "shape": feature["geometry"],
                "metadata": feature["properties"],
                "division_id": feature["properties"]["ocdid"],
                "year": year,
                "extent": [],
                "centroid": {
                    "coordinates": [
                        gdf["geometry"].centroid.x[0],
                        gdf["geometry"].centroid.y[0],
                    ],
                    "type": "Point",
                },
            }
            with open(f"{ROOTDIR}/data/boundaries/{folder}/{filename}.json", "w") as f:
                json.dump(obj, f)
    # all geojson files processed...now to upload
    print("Uploading division files to S3")
    s3 = boto3.client("s3")
    bucket = "data.openstates.org"
    prefix_path = "data/boundaries"
    for file in glob.glob(f"{ROOTDIR}/{prefix_path}/**/*.json", recursive=True):
        print(f"{file=}")
        exit(1)
        path = "boundaries/{YEAR}/"
        s3.put_object(Body=open(file, "r").read(), Bucket=bucket, Key=path)
    # s3.chmod(bucket_path, acl="public-read", recursive=True)
    print("Please ensure `public-read` ACL is set on the new data in S3")


if __name__ == "__main__":
    main()
