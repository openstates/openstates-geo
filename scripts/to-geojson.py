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
    if district_type == "cong":
        district_type = "cd"
    state = state.lower()
    state_meta = metadata.lookup(abbr=state)
    mapping_key = settings["jurisdictions"][state_meta.name]["id-mappings"][
        district_type
    ]["key"]
    output_filename = f"{ROOTDIR}/data/geojson/{state}-{district_type}.geojson"
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
        if not district_id or district_id == "None":
            print("Empty district ID? Skipping")
            continue
        if district_id == "ZZZ":
            print("Bad TIGER district ID. Skipping")
            continue

        # geoid code has to be FIPS + 3 character code, so we pad with 0
        district_padding = "0" * (3 - len(district_id))
        geoid = f"{district_type}-{state_meta.fips}{district_padding}{district_id}"
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
            prefix = mapping_type.get("os-id-prefix", None)
            if not prefix:
                prefix = mappings["os-id-prefix"]
                ocd_id = f"{prefix}/{district_type}:{district_id}".lower()
            else:
                ocd_id = f"{prefix}{district_id}".lower()

        if district_type == "cd":
            if district_id.lower() == "at-large":
                district_name = f"{state.upper()}-AL"
            else:
                district_name = f"{state.upper()}-{district_id}"
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

    output_filename = f"{ROOTDIR}/data/geojson/{state}-{district_type}.geojson"
    print(f"{geojson_path} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geojson, geojson_file)


def process_territories(cd_file: str, settings: dict):
    """
    Convert TIGER data to properly formatted territory
    information
    """
    print("Processing TIGER data for territory districts")
    territories = [t for t in us.TERRITORIES + [us.states.DC]]
    with open(cd_file, "r") as f:
        rawgeodata = json.load(f)
    territory_geo = {k: v for k, v in rawgeodata.items() if k not in ["features"]}
    territory_geo["features"] = []
    for district in rawgeodata["features"]:
        fips = district["properties"]["STATEFP"]
        territory = None
        for t in territories:
            if fips == t.fips:
                territory = t
                break
        else:
            continue
        try:
            _ = metadata.lookup(abbr=territory.abbr)
        except Exception:
            print(f"{territory.name} not defined in OpenStates metadata. Skipping")
            continue
        geoid = district["properties"]["GEOID"]
        if geoid.endswith("98") or geoid.endswith("99"):
            geoid = "at-large"
        district_padding = "0" * (3 - len(geoid))
        district_id = f"cd-{district_padding}{geoid}"
        mappings = settings["jurisdictions"][territory.name]
        custom = mappings["id-mappings"].get("custom", [])
        mapping_type = mappings["id-mappings"]["cd"]
        ocd_id = None
        for mapping in custom:
            if mapping.get("sld-id", "") == geoid:
                ocd_id = mapping["os-id"]
                break
        if not ocd_id:
            prefix = mapping_type.get("os-id-prefix", None)
            if prefix:
                ocd_id = prefix.lower()
            else:
                prefix = mappings["os-id-prefix"]
                ocd_id = prefix.lower()

        if district_id.lower().endswith("at-large"):
            district_name = f"{territory.abbr.upper()}-AL"
        else:
            district_name = f"{territory.abbr.upper()}-{geoid}"

        district["properties"] = {
            "ocdid": ocd_id,
            "type": "cd",
            "state": territory.abbr,
            "name": district_name,
        }
        territory_geo["features"].append(district)
    output_filename = f"{ROOTDIR}/data/geojson/us-cd.geojson"
    print(f"{cd_file} (territories only) => {output_filename}")
    with open(output_filename, "w") as f:
        json.dump(territory_geo, f)


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
        if SETTINGS["us_cd_file"] not in newfilename:
            merge_ids(newfilename, SETTINGS)
    process_territories(
        f"{ROOTDIR}/data/source_cache/us_cd_2022-tiger/{SETTINGS['us_cd_file']}",
        SETTINGS,
    )
