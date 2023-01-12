#!/usr/bin/env python3

from datetime import datetime
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
            metadata = dict(feature["properties"])
            folder, filename = metadata["ocdid"].rsplit("/", 1)
            full_path = f"{ROOTDIR}/data/boundaries/{folder}/{filename}.json"
            if os.path.exists(full_path):
                print(f"{filename}.json already exists. Skipping.")
            os.makedirs(f"{ROOTDIR}/data/boundaries/{folder}", exist_ok=True)
            obj = {
                "shape": feature["geometry"],
                "metadata": metadata,
                "division_id": metadata["ocdid"],
                "year": year,
                "extent": [],
                "centroid": [],
            }
            with open(f"{ROOTDIR}/data/boundaries/{folder}/{filename}.json", "w") as f:
                json.dump(obj, f)


if __name__ == "__main__":
    main()
