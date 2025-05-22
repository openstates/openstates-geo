import copy
import glob
import json
import openstates.metadata as metadata
import os
import re
import subprocess

from .general import (
    JURISDICTIONS,
    ROOTDIR,
    print_script_progress,
)

FIPS_KEYS = (
    "STATEFP",
    "STATEFP20",
    "STATEFP"  # Used in shapefiles from https://www2.census.gov/geo/tiger/GENZ2024/shp/
)
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


def convert_to_geojson(SETTINGS: dict) -> None:
    print("convert_to_geojson: find source_cache/**/*.shp")
    files = glob.glob(f"{ROOTDIR}/data/source_cache/**/*.shp", recursive=True)
    for file in files:
        newfilename = file.replace(".shp", ".geojson")
        if os.path.exists(newfilename):
            print(f"convert_to_geojson: {newfilename} already exists, skipping")
        else:
            print(f"convert_to_geojson: Converting {file} => {newfilename}")
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
            _merge_ids(newfilename, SETTINGS)


def _merge_ids(geojson_path: str, settings: dict) -> None:
    print_script_progress(f"convert_to_geojson: _merge_ids for {geojson_path}")
    with open(geojson_path, "r") as f:
        rawgeodata = json.load(f)
    geodata = {k: v for k, v in rawgeodata.items() if k not in ["features"]}
    geodata["features"] = []
    for district in rawgeodata["features"]:
        fips = _find_key(district["properties"], FIPS_KEYS)
        if not fips:
            print(f"_merge_ids: {fips} not defined in metadata. Skipping")
            continue
        """
        Find the matching jurisdiction based on FIPS code
        """
        # print(f"_merge_ids: Find the matching jurisdiction based on FIPS code {fips}")
        for j in JURISDICTIONS:
            if fips == j.fips:
                juris = j
                break
        else:
            print(f"_merge_ids: {fips} not defined in metadata. Skipping")
            continue
        state_meta = metadata.lookup(abbr=juris.abbr)
        mtfcc_type_from_mtfcc_property = _find_key(district["properties"], MTFCC_KEYS)
        if mtfcc_type_from_mtfcc_property:
            dt = settings["MTFCC_MAPPING"][mtfcc_type_from_mtfcc_property].lower()
        else:
            # See if we can fallback to getting district type from filename
            if "sldl" in geojson_path:
                print(f"_merge_ids: got district type 'sldl' from filename {geojson_path}")
                dt = "sldl"
            elif "sldu" in geojson_path:
                print(f"_merge_ids: got district type 'sldu' from filename {geojson_path}")
                dt = "sldu"
            else:
                print(f"_merge_ids: failed to find district type in geojson district properties {district['properties']}")
                continue
        mappings = settings["jurisdictions"][juris.name]["id-mappings"]
        if "sld-prefix" in mappings[dt]:
            district_type = mappings[dt]["sld-prefix"]
        else:
            district_type = dt
        ocd_prefix = settings["jurisdictions"][juris.name]["os-id-prefix"]
        geoid = _find_key(district["properties"], GEOID_KEYS)
        if not geoid or geoid in settings["SKIPPED_GEOIDS"] or geoid.endswith("ZZ"):
            print(f"_merge_ids: Skipping bad geoid: {geoid} in {juris.name} file {geojson_path}")
            continue
        census_id = f"{district_type}-{geoid}"
        ocd_id = None
        for custom_match in mappings.get("custom", []):
            if "sld-id" not in custom_match:
                continue
            if census_id == custom_match["sld-id"]:
                ocd_id = custom_match["os-id"]
                break
        if not ocd_id:
            try:
                di_match = re.compile(mappings[district_type]["sld-match"])
            except Exception:
                print(f"_merge_ids: Missing any way to classify {census_id}")
                continue
            sld_id = di_match.search(census_id)
            if not sld_id:
                print(f"_merge_ids: {census_id} doesn't match any districts with {di_match}")
                continue
            sld_id = sld_id.groups()[0]
            ocd_id = f"{ocd_prefix}/{district_type}:{sld_id.lstrip('0')}".lower()
        if district_type == "cd":
            """
            Federal files have some quirks that other jurisdictional boundaries
            don't have. Particularly:
            1. the actual district name
            2. handling "at large" districts
            """
            cd_num = geoid.removeprefix(fips)
            if cd_num in ["00", "98"]:
                ocd_id = f"{ocd_prefix}/{district_type}:at-large"
                district_name = f"{juris.abbr.upper()}-AL"
            else:
                ocd_id = f"{ocd_prefix}/{district_type}:{int(cd_num)}"
                district_name = f"{juris.abbr.upper()}-{cd_num}"
        else:
            # Jurisdictional boundaries we can look up in OpenStates
            if not mappings[district_type].get("split_districts", False):
                district_meta = state_meta.lookup_district(ocd_id)
                if not district_meta:
                    print(f"_merge_ids: Couldn't find metadata for {ocd_id}")
                    exit(1)
                district_name = district_meta.name

        if mappings[district_type].get("split_districts", False):
            district_name = ocd_id.split(":")[1]
            for key in ["a", "b"]:
                this_district = copy.deepcopy(district)
                this_district["properties"]["ocdid"] = f"{ocd_id}{key}"
                this_district["properties"]["type"] = dt
                this_district["properties"]["state"] = juris.abbr
                this_district["properties"]["name"] = f"{district_name}{key.upper()}"
                geodata["features"].append(this_district)
        else:
            district["properties"]["ocdid"] = ocd_id
            district["properties"]["type"] = dt
            district["properties"]["state"] = juris.abbr
            district["properties"]["name"] = district_name
            geodata["features"].append(district)

    output_filename = f"{ROOTDIR}/data/geojson/{juris.abbr}-{dt}.geojson"
    print_script_progress(f"_merge_ids: Writing data from {geojson_path} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geodata, geojson_file)
