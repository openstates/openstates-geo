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

from utils import JURISDICTIONS, ROOTDIR, setup_source, load_settings

FIPS_KEYS = ("STATEFP", "STATEFP20")
GEOID_KEYS = ("GEOID", "GEOID20")
MTFCC_KEYS = ("MTFCC", "MTFCC20")


def _find_key(district_properties, keys):
    for key in keys:
        fips = district_properties.get(key, None)
        if fips:
            return fips
    else:
        print(f"Couldn't find {keys} in {district_properties}")
        return None


def merge_ids(geojson_path, settings):
    with open(geojson_path, "r") as f:
        rawgeodata = json.load(f)
    geodata = {k: v for k, v in rawgeodata.items() if k not in ["features"]}
    geodata["features"] = []
    jurisdiction = None
    district_type = None
    for district in rawgeodata["features"]:
        fips = _find_key(district["properties"], FIPS_KEYS)
        if not fips:
            continue
        """
        Find the matching jurisdiction district
        """
        for j in JURISDICTIONS:
            if fips == j.fips:
                jurisdiction = j
                break
        else:
            continue
        try:
            _ = metadata.lookup(abbr=jurisdiction.abbr)
        except Exception:
            print(f"{jurisdiction.name} not defined in OpenStates metadata. Skipping")
            continue
        if not district_type:
            mapping = _find_key(district["properties"], MTFCC_KEYS)
            if not mapping:
                continue
            district_type = settings["MTFCC_MAPPING"][mapping]
        geoid = _find_key(district["properties"], GEOID_KEYS)
        if not geoid or geoid in settings["SKIPPED_GEOIDS"]:
            continue
        if geoid.endswith("98") or geoid.endswith("99"):
            geoid = "at-large"
        district_padding = "0" * (3 - len(geoid))
        district_id = f"cd-{district_padding}{geoid}"
        mappings = settings["jurisdictions"][jurisdiction.name]
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
            district_name = f"{jurisdiction.abbr.upper()}-AL"
        else:
            district_name = f"{jurisdiction.abbr.upper()}-{geoid}"

        district["properties"]["ocdid"] = ocd_id
        district["properties"]["type"] = "cd"
        district["properties"]["state"] = jurisdiction.abbr
        district["properties"]["name"] = district_name
        geodata["features"].append(district)

    output_filename = (
        f"{ROOTDIR}/data/geojson/{jurisdiction.abbr}-{district_type}.geojson"
    )
    print(f"Writing data from {geojson_path} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geodata, geojson_file)


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
            continue
        else:
            print(f"Converting {file} => {newfilename}")
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
