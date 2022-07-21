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

SKIPPED_GEOIDS = {
    "cd-6098": "American Samoa",
    "cd-6998": "Northern Mariana Islands",
    "cd-6698": "Guam",
    "cd-7898": "Virgin Islands",
}


def get_ocdid_records():
    paths = [
        "./data/ocdids/us_sldu.csv",
        "./data/ocdids/us_sldl.csv",
        "./data/ocdids/us_cd.csv",
    ]
    all_divs = []
    for path in paths:
        with open(path, "r") as div_file:
            reader = csv.DictReader(div_file)
            all_divs += [row for row in reader]
    return all_divs


ocd_ids = get_ocdid_records()

MTFCC_MAPPING = {
    "G5200": "cd",
    "G5210": "sldu",
    "G5220": "sldl",
}


def merge_ids(geojson_path):
    with open(geojson_path, "r") as geojson_file:
        geojson = json.load(geojson_file)

    for feature in geojson["features"]:
        district_type = MTFCC_MAPPING[feature["properties"]["MTFCC"]]

        # Identify the OCD ID by making a lookup against the CSV files
        # The OCD ID is the cannonical identifier of an area on
        # the Open States platform
        geoid = "{}-{}".format(district_type, feature["properties"]["GEOID"])

        if geoid in SKIPPED_GEOIDS:
            continue

        for row in ocd_ids:
            if row["census_geoid"] == geoid:
                ocd_id = row["id"]
                break
        else:
            print(feature["properties"])
            raise AssertionError("Could not find OCD ID for GEOID {}".format(geoid))

        # Although OCD IDs contain the state postal code, parsing
        # an ID to determine structured data is bad practice,
        # so add a standalone state postal abbreviation property too
        state = us.states.lookup(feature["properties"]["STATEFP"]).abbr.lower()
        state_meta = metadata.lookup(abbr=state)
        if ocd_id in OCD_FIXES:
            ocd_id = OCD_FIXES[ocd_id]

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
    try:
        os.makedirs("./data/geojson")
    except FileExistsError:
        pass

    expected = 103
    if len(sys.argv) == 1:
        files = sorted(glob.glob("data/source/tl*.shp"))
        if len(files) != expected:
            raise AssertionError(f"Expecting {expected} shapefiles, got {len(files)}).")
    else:
        files = sys.argv[1:]

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
                    "GEOID NOT LIKE '%ZZ'",
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
