#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import json
import openstates.metadata as metadata
import os
import subprocess
import sys
import us
import yaml

from utils import JURISDICTION_NAMES, ROOTDIR, setup_source

SKIPPED_GEOIDS = {
    "cd-6098": "American Samoa",
    "cd-6998": "Northern Mariana Islands",
    "cd-6698": "Guam",
    "cd-7898": "Virgin Islands",
}


MTFCC_MAPPING = {
    "G5200": "cd",
    "G5210": "sldu",
    "G5220": "sldl",
}


def _load_id_mappings(path: str):
    with open(path, "r") as f_in:
        all_divs = yaml.safe_load(f_in.read())
    return all_divs


def merge_ids(geojson_path):
    with open(geojson_path, "r") as geojson_file:
        geojson = json.load(geojson_file)

    for feature in geojson["features"]:
        district_type = MTFCC_MAPPING[feature["properties"]["MTFCC"]]

        # Identify the OCD ID by making a lookup against the CSV files
        # The OCD ID is the cannonical identifier of an area on
        # the Open States platform
        geoid = f"{district_type}-{feature['properties']['geoid']}"

        if geoid in SKIPPED_GEOIDS:
            continue

        # for row in ocd_ids:
        #     if row["census_geoid"] == geoid:
        #         ocd_id = row["id"]
        #         break
        # else:
        #     print(feature["properties"])
        #     raise AssertionError(f"Could not find OCD ID for GEOID {geoid}")

        # Although OCD IDs contain the state postal code, parsing
        # an ID to determine structured data is bad practice,
        # so add a standalone state postal abbreviation property too
        state = us.states.lookup(feature["properties"]["STATEFP"]).abbr.lower()
        state_meta = metadata.lookup(abbr=state)
        ocd_id = 1

        if district_type == "cd":
            cd_num = feature["properties"]["CD116FP"]
            if cd_num in ("00", "98"):
                cd_num = "AL"
            district_name = f"{state.upper()}-{cd_num}"
        else:
            district = state_meta.lookup_district(ocd_id)
            district_name = district.name
            if not district:
                raise ValueError(f"no {ocd_id} {district_type}")

        # relying on copy-by-reference to update the actual parent object
        feature["properties"] = {
            "ocdid": ocd_id,
            "type": district_type,
            "state": state,
            "name": district_name,
        }

    if district_type == "cd":
        output_filename = f"data/geojson/us-{district_type}.geojson"
    else:
        output_filename = f"data/geojson/{state}-{district_type}.geojson"
    print(f"{geojson_path} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geojson, geojson_file)


if __name__ == "__main__":
    setup_source()
    mappings = _load_id_mappings(f"{ROOTDIR}/id-mappings.yml")

    if len(sys.argv) == 1:
        files = sorted(glob.glob(f"{ROOTDIR}/data/source/**/*.shp", recursive=True))
    else:
        files = sys.argv[1:]

    for file in files:

        newfilename = file.replace(".shp", ".geojson")
        if os.path.exists(newfilename):
            print(newfilename, "already exists, skipping")
        else:
            print(f"{file} => {newfilename}")
            subprocess.run(
                [
                    "ogr2ogr",
                    # "-where",
                    # "GEOID NOT LIKE '%ZZ'",
                    "-t_srs",
                    "crs:84",
                    "-f",
                    "GeoJSON",
                    newfilename,
                    file,
                ],
                check=True,
            )
        meta_file = file.replace(".shp", ".dbf").lower()
        new_meta = meta_file.replace(".dbf", "_meta.geojson")
        if os.path.exists(meta_file):
            print(f"{meta_file} => {new_meta}")
            subprocess.run(
                [
                    "ogr2ogr",
                    # "-where",
                    # "GEOID NOT LIKE '%ZZ'",
                    "-t_srs",
                    "crs:84",
                    "-f",
                    "GeoJSON",
                    new_meta,
                    meta_file,
                ],
                check=True,
            )
        # merge_ids(newfilename)
