#!/usr/bin/env python3
import csv
import json
import glob
import us


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

        # The source shapefiles have a large number of properties,
        # but the output tiles only need these three for their
        # use on openstates.org; this helps keep down the MBTiles
        # file size
        feature["properties"] = {"ocdid": ocd_id, "type": district_type, "state": state}

    output_filename = f"final-geojson/{state}-{district_type}.geojson"
    with open(output_filename, "w") as geojson_file:
        json.dump(geojson, geojson_file)


if __name__ == "__main__":
    for fname in glob.glob("data/*.geojson"):
        merge_ids(fname)
