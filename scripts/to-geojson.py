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


def _tiger_geoid(geojson, settings, geojson_path):
    """
    Process a GeoJSON file sent from TIGER.
    """
    for feature in geojson["features"]:
        mtfcc = feature["properties"].get("MTFCC")
        geoid = feature["properties"].get("GEOID")
        if "ZZ" in geoid:
            continue
        district_type = settings["MTFCC_MAPPING"][mtfcc]

        geoid = f"{district_type}-{geoid}"
        if geoid in settings["SKIPPED_GEOIDS"]:
            continue

        state = us.states.lookup(feature["properties"]["STATEFP"]).abbr.lower()
        state_name = us.states.lookup(feature["properties"]["STATEFP"]).name
        state_meta = metadata.lookup(abbr=state)

        """
        So we first get our mappings for the current jurisdiction
        Then we compare mappings.
        Custom mappings must come first, or we may end up with in-accurate
        associations.
        And we should only check regex matching if custom mappings fail.
        """
        mappings = settings["jurisdictions"][state_name]
        print(f"{mappings=}")
        custom = mappings["id-mappings"].get("custom", [])
        mapping_type = mappings["id-mappings"][district_type]
        ocd_id = None
        for mapping in custom:
            if mapping.get("sld-id", "") == geoid:
                ocd_id = mapping["os-id"]
                break
        if not ocd_id:
            dist_id = re.search(mapping_type["sld-match"], geoid).groups()[0]
            ocd_id = f"{mapping_type['os-id-prefix']}{dist_id}"

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


def _arp_geoid(geojson, settings, geojson_path):
    for feature in geojson["features"]:


def merge_ids(geojson_path: str, meta_file: str, settings: dict):
    print(f"Converting IDs for {geojson_path}...")
    with open(geojson_path, "r") as f:
        geojson = json.load(f)
    prefix = geojson_path.rsplit(".", 1)[0]
    meta_path = f"{prefix}_meta.geojson"
    metajson = None
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            metajson = json.load(f)
    elif os.path.exists(meta_path.lower()):
        meta_path = meta_path.lower()
        with open(meta_path, "r") as f:
            metajson = json.load(f)

    """
    First, check for TIGER-style setup
    """
    mtfcc = geojson["features"][0]["properties"].get("MTFCC", None)
    geoid = geojson["features"][0]["properties"].get("GEOID", None)
    if mtfcc and geoid:
        _tiger_geoid(geojson, settings, geojson_path)
    else:
        if metajson and not geojson["features"][0]["properties"]:
            print(f"Adding metadata from {meta_path} to {geojson_path}")
            for geo_feat, meta_feat in zip(geojson["features"], metajson["features"]):
                geo_feat["properties"] = meta_feat["properties"]
        _arp_geoid(geojson, settings, geojson_path)
        exit(1)


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
            # print(f"{newfilename} already exists, skipping")
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
        """
        Why name things consistently?
        There maybe a dbf file with all lowercase
        _or_ casing consistent with the shp file
        """
        meta_file = file.replace(".shp", ".dbf")
        new_meta = meta_file.replace(".dbf", "_meta.geojson")
        meta_file_lower = meta_file.lower()
        new_meta_lower = new_meta.lower()
        if os.path.exists(meta_file):
            if os.path.exists(new_meta):
                # print(f"{new_meta} already exists, skipping")
                pass
            else:
                print(f"{meta_file} => {new_meta}")
                subprocess.run(
                    [
                        "ogr2ogr",
                        "-t_srs",
                        "crs:84",
                        "-f",
                        "GeoJSON",
                        new_meta,
                        meta_file,
                    ],
                    check=True,
                )
        elif os.path.exists(meta_file_lower):
            meta_file = meta_file_lower
            new_meta = new_meta_lower
            if os.path.exists(new_meta_lower):
                # print(f"{new_meta_lower} already exists, skipping")
                pass
            else:
                print(f"{meta_file_lower} => {new_meta_lower}")
                subprocess.run(
                    [
                        "ogr2ogr",
                        "-t_srs",
                        "crs:84",
                        "-f",
                        "GeoJSON",
                        new_meta_lower,
                        meta_file_lower,
                    ],
                    check=True,
                )
        merge_ids(newfilename, new_meta, SETTINGS)
