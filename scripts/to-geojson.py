#!/usr/bin/env python3
import os
import sys
import csv
import json
import glob
import subprocess
import us
import openstates_metadata as metadata

OCD_FIXES = {
    "ocd-division/country:us/state:vt/sldu:grand_isle-chittenden": "ocd-division/country:us/state:vt/sldu:grand_isle"
}


def get_ocdid_records():
    SLDU_CSV_PATH = "./data/us_sldu.csv"
    with open(SLDU_CSV_PATH, "r") as sldu_file:
        reader = csv.DictReader(sldu_file)
        sldu = [row for row in reader]

    SLDL_CSV_PATH = "./data/us_sldl.csv"
    with open(SLDL_CSV_PATH, "r") as sldl_file:
        reader = csv.DictReader(sldl_file)
        sldl = [row for row in reader]

    return sldu + sldl


ocd_ids = get_ocdid_records()


def merge_ids(geojson_path):
    with open(geojson_path, "r") as geojson_file:
        geojson = json.load(geojson_file)

    for feature in geojson["features"]:
        district_type = "sldu" if feature["properties"]["MTFCC"] == "G5210" else "sldl"

        # Identify the OCD ID by making a lookup against the CSV files
        # The OCD ID is the cannonical identifier of an area on
        # the Open States platform
        geoid = "{}-{}".format(district_type, feature["properties"]["GEOID"])
        for row in ocd_ids:
            if row["census_geoid_14"] == geoid:
                ocd_id = row["id"]
                break
        else:
            raise AssertionError("Could not find OCD ID for GEOID {}".format(geoid))

        # Although OCD IDs contain the state postal code, parsing
        # an ID to determine structured data is bad practice,
        # so add a standalone state postal abbreviation property too
        state = us.states.lookup(feature["properties"]["STATEFP"]).abbr.lower()
        state_meta = metadata.lookup(abbr=state)
        if ocd_id in OCD_FIXES:
            ocd_id = OCD_FIXES[ocd_id]
        district = state_meta.lookup_district(ocd_id)
        if not district:
            raise ValueError(f"no {ocd_id} {district_type}")
            continue

        feature["properties"] = {
            "ocdid": ocd_id,
            "type": "sldl",
            "state": state,
            "name": district.name,
        }

    output_filename = f"data/geojson/{state}-{district_type}.geojson"
    print(f"{geojson_path} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geojson, geojson_file)


def process_va_lower(file):
    newfilename = file.replace(".shp", ".geojson")
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
    with open(newfilename, "r") as geojson_file:
        geojson = json.load(geojson_file)

    state = "va"
    district_type = "sldl"

    for feature in geojson["features"]:
        n = feature["properties"]["District_N"]
        feature["properties"] = {
            "ocdid": f"ocd-division/country:us/state:va/sldl:{n}",
            "type": district_type,
            "state": state,
            "name": str(n),
        }

    output_filename = f"data/geojson/{state}-{district_type}.geojson"
    print(f"{newfilename} => {output_filename}")
    with open(output_filename, "w") as geojson_file:
        json.dump(geojson, geojson_file)


if __name__ == "__main__":
    try:
        os.makedirs("./data/geojson")
    except FileExistsError:
        pass

    expected = 101
    if len(sys.argv) == 1:
        files = sorted(glob.glob("data/source/tl*.shp"))
        if len(files) != expected:
            raise AssertionError(f"Expecting {expected} shapefiles, got {len(files)}).")
    else:
        files = sys.argv[1:]

    process_va_lower("data/source/va_lower_remedial_2019.shp")
    1/0

    for file in files:
        newfilename = file.replace(".shp", ".geojson")
        if os.path.exists(newfilename):
            print(newfilename, "already exists, skipping")
        else:
            print(file, "=>", newfilename)
            subprocess.run(
                [
                    "ogr2ogr",
                    "-where",
                    "GEOID NOT LIKE '%ZZZ'",
                    "-t_srs",
                    "crs:84",
                    "-f",
                    "GeoJSON",
                    newfilename,
                    file,
                ],
                check=True,
            )
        merge_ids(newfilename)
