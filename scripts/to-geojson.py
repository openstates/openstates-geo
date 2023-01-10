#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import json
import openstates.metadata as metadata
import os
import re
import subprocess
import sys
import us
import yaml

from utils import JURISDICTION_NAMES, ROOTDIR, setup_source, load_settings

POSSIBLE_KEYS = ["DISTRICT", "SEN_DIST"]

def merge_ids(geojson_path: str, settings: dict):
    print(f"Converting IDs for {geojson_path}...")
    with open(geojson_path, "r") as f:
        geojson = json.load(f)
    print(f"{len(geojson['features'])} features in {geojson_path}")
    folder = geojson_path.split("/")[-2]
    state, district_type = folder.split("_")[:2]
    state_meta = metadata.lookup(abbr=state)
    state_name = state_meta.name
    state_fips = state_meta.fips
    for feature in geojson["features"]:
        print(f"Processing {feature['properties']}")
        for key in POSSIBLE_KEYS:
            district_id = feature["properties"].get(key, None)
            if district_id:
                break
        district_padding = "0" * (3 - len(district_id))
        geoid = f"{district_type}-{state_fips}{district_padding}{district_id}"
        if geoid in settings["SKIPPED_GEOIDS"]:
            continue

        """
        So we first get our mappings for the current jurisdiction
        Then we compare mappings.
        Custom mappings must come first, or we may end up with inaccurate
        associations.
        And we should only check regex matching if custom mappings fail.
        """
        mappings = settings["jurisdictions"][state_name]
        custom = mappings["id-mappings"].get("custom", [])
        mapping_type = mappings["id-mappings"][district_type]
        ocd_id = None
        dist_id = None
        for mapping in custom:
            if mapping.get("sld-id", "") == geoid:
                ocd_id = mapping["os-id"]
                break
        if not ocd_id:
            dist_id = re.search(mapping_type["sld-match"], geoid).groups()[0]
            # cleanest way to strip leading 0s
            if mapping_type.get("match_type", "int") == "int":
                dist_id = int(dist_id)
            ocd_id = f"{mapping_type['os-id-prefix']}{dist_id}".lower()

        if district_type == "cd":
            cd_num = feature["properties"]["CD116FP"]
            """
            00 and 98 correlate to "at-large" districts
            """
            if cd_num in ("00", "98"):
                cd_num = "AL"
            district_name = f"{state.upper()}-{cd_num}"
        else:
            district = state_meta.lookup_district(ocd_id)
            if not district:
                raise ValueError(f"no {ocd_id} {district_type} {dist_id}")
            district_name = district.name

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
    SETTINGS = load_settings(f"{ROOTDIR}/configs")

    if len(sys.argv) == 1:
        files = glob.glob(f"{ROOTDIR}/data/source_cache/**/*.shp", recursive=True)
    else:
        files = sys.argv[1:]

    for file in files:

        newfilename = file.replace(".shp", ".geojson")
        if os.path.exists(newfilename):
            print(f"{newfilename} already exists, skipping")
            pass
        else:
            print(f"{file} => {newfilename}")
            subprocess.run(
                [
                    "ogr2ogr",
                    "-t_srs",
                    "crs:84",
                    "-f",
                    "GeoJSON",
                    newfilename,
                    file,
                ],
                check=True,
            )
        merge_ids(newfilename, SETTINGS)
