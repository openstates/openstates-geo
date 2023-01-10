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


def merge_ids(geojson_path: str, settings: dict):
    folder = geojson_path.split("/")[-2]
    state, district_type = folder.split("_")[:2]
    if state in ["ma", "vt"]:
        print("Skipping MA and VT for now")
        return
    state_meta = metadata.lookup(abbr=state)
    mapping_key = settings["jurisdictions"][state_meta.name]["id-mappings"][
        district_type
    ]["key"]
    output_filename = f"data/geojson/{state}-{district_type}.geojson"
    if os.path.exists(output_filename):
        print(f"Final geojson for {state},{district_type} already exists. Skipping")
        return
    print(f"Converting IDs for {geojson_path}...")
    with open(geojson_path, "r") as f:
        geojson = json.load(f)
    print(f"{len(geojson['features'])} features in {geojson_path}")
    for feature in geojson["features"]:
        print(f"Processing {feature['properties']}")
        district_id = str(feature["properties"].get(mapping_key, None)).lstrip("0")
        if not district_id:
            print(f"District with empty ID: {feature['properties']}. Skipping.")
            continue
        if district_type == "sldu" and state in ["md", "mo"]:
            district_id = district_id.lstrip("SD").lstrip("0")
        if state in ["nv", "ut"]:
            district_id = str(int(float(district_id)))
        print(f"{district_id=}")

        # geoid code has to be FIPS + 3 character code, so we pad with 0
        district_padding = "0" * (3 - len(district_id))
        geoid = f"{district_type}-{state_meta.fips}{district_padding}{district_id}"
        print(f"Processing {district_id=}, {geoid}")
        if geoid in settings["SKIPPED_GEOIDS"]:
            continue

        """
        So we first get our mappings for the current jurisdiction
        Then we compare mappings.
        Custom mappings must come first, or we may end up with inaccurate
        associations.
        And we should only check regex matching if custom mappings fail.
        """
        mappings = settings["jurisdictions"][state_meta.name]
        custom = mappings["id-mappings"].get("custom", [])
        mapping_type = mappings["id-mappings"][district_type]
        ocd_id = None
        for mapping in custom:
            if mapping.get("sld-id", "") == geoid:
                ocd_id = mapping["os-id"]
                break
        if not ocd_id:
            ocd_id = f"{mapping_type['os-id-prefix']}{district_id}".lower()

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
                raise ValueError(f"no {ocd_id} {district_type} {district_id}")
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
