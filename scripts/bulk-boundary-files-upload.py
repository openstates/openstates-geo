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
            subpath = feature["properties"]["ocdid"]
            full_path = f"{ROOTDIR}/data/boundaries/{subpath}.json"
            if os.path.exists(full_path):
                continue
            folder = "/".join(subpath.split("/")[:-1])
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
            with open(full_path, "w") as f:
                json.dump(obj, f)

    # all geojson files processed...now to upload
    print("Uploading division files to S3")
    s3 = boto3.resource("s3")
    bucket = "data.openstates.org"
    prefix_path = f"{ROOTDIR}/data/boundaries"
    bucket_path = f"boundaries/{year}"
    for index, file in enumerate(glob.glob(f"{prefix_path}/**/*.json", recursive=True)):
        path = file.removeprefix(f"{prefix_path}/")
        path = f"{bucket_path}/{path}"
        s3.Object(bucket, path).put(Body=open(file, "r").read(), ACL="public-read")
        if index and index % 50 == 0:
            print(f"Processed {index} files...")


if __name__ == "__main__":
    main()
