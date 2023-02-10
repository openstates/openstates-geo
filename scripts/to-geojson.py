#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import glob
import json
import openstates.metadata as metadata
import os
import re
import subprocess
import sys
import yaml

from utils import JURISDICTIONS, ROOTDIR, setup_source, load_settings

FIPS_KEYS = ("STATEFP", "STATEFP20")
GEOID_KEYS = ("GEOID", "GEOID20")
MTFCC_KEYS = ("MTFCC", "MTFCC20")


def _find_key(district_properties, keys):
    for key in keys:
        res = district_properties.get(key, None)
        if res:
            return res
    else:
        print(f"Couldn't find {keys} in {district_properties}")
        return None


def merge_ids(geojson_path, settings):
    with open(geojson_path, "r") as f:
        rawgeodata = json.load(f)
    geodata = {k: v for k, v in rawgeodata.items() if k not in ["features"]}
    geodata["features"] = []
    for district in rawgeodata["features"]:
        fips = _find_key(district["properties"], FIPS_KEYS)
        if not fips:
            continue
        """
        Find the matching jurisdiction district
        """
        for j in JURISDICTIONS:
            if fips == j.fips:
                juris = j
                break
        else:
            print(f"{fips} not defined in metadata. Skipping")
            continue
        state_meta = metadata.lookup(abbr=juris.abbr)
        res = _find_key(district["properties"], MTFCC_KEYS)
        if not res:
            continue
        district_type = settings["MTFCC_MAPPING"][res].lower()
        mappings = settings["jurisdictions"][juris.name]["id-mappings"]
        if "os-id-prefix" in mappings[district_type]:
            ocd_prefix = mappings[district_type]["os-id-prefix"]
        else:
            ocd_prefix = settings["jurisdictions"][juris.name]["os-id-prefix"]
        geoid = _find_key(district["properties"], GEOID_KEYS)
        if not geoid or geoid in settings["SKIPPED_GEOIDS"]:
            continue
        census_id = f"{district_type}-{geoid}"
        ocd_id = None
        for custom_match in mappings.get("custom", []):
            if census_id == custom_match["sld-id"]:
                ocd_id = custom_match["os-id"]
                break
        if not ocd_id:
            di_match = re.compile(mappings[district_type]["sld-match"])
            sld_id = di_match.search(census_id)
            if not sld_id:
                print(f"{census_id} doesn't match any districts with {di_match}")
                continue
            sld_id = sld_id.groups()[0]
            ocd_id = f"{ocd_prefix}/{district_type}:{sld_id.lstrip('0')}".lower()
        if district_type == "cd":
            cd_num = geoid.removeprefix(fips)
            if cd_num in ["00", "98"]:
                ocd_id = f"{ocd_prefix}/{district_type}:at-large"
                district_name = f"{juris.abbr.upper()}-AL"
            else:
                ocd_id = f"{ocd_prefix}/{district_type}:{int(cd_num)}"
                district_name = f"{juris.abbr.upper()}-{cd_num}"
        else:
            output_filename = f"data/geojson/{juris.abbr}-{district_type}.geojson"
            district_meta = state_meta.lookup_district(ocd_id)
            if not district_meta:
                print(f"Missing district for {ocd_id}")
                continue
            district_name = district_meta.name

        district["properties"]["ocdid"] = ocd_id
        district["properties"]["type"] = district_type
        district["properties"]["state"] = juris.abbr
        district["properties"]["name"] = district_name
        geodata["features"].append(district)

    if district_type == "cd":
        output_filename = f"data/geojson/us-{district_type}.geojson"
    else:
        output_filename = f"{ROOTDIR}/data/geojson/{juris.abbr}-{district_type}.geojson"
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
