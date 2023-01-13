#!/usr/bin/env python3

from datetime import datetime
import geopandas as gpd
import glob
import json
import os
from s3fs import S3FileSystem

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
            folder, filename = feature["properties"]["ocdid"].rsplit("/", 1)
            full_path = f"{ROOTDIR}/data/boundaries/{folder}/{filename}.json"
            if os.path.exists(full_path):
                print(f"{filename}.json already exists. Skipping.")
                continue
            gdf = gpd.GeoDataFrame.from_features([feature])
            os.makedirs(f"{ROOTDIR}/data/boundaries/{folder}", exist_ok=True)
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
    s3 = S3FileSystem(anon=False)
    bucket_path = f"data.openstates.org/boundaries/{year}"
    print("Uploading division files to S3")
    s3.put(f"{ROOTDIR}/data/boundaries/", bucket_path, recursive=True)
    s3.chmod(bucket_path, acl="public-read", recursive=True)


if __name__ == "__main__":
    main()
