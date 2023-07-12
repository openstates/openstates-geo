#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from django.core.management import execute_from_command_line
import os

from utils import (
    JURISDICTION_NAMES,
    ROOTDIR,
    bulk_upload,
    convert_to_geojson,
    create_tiles,
    download_from_tiger,
    download_boundary_file,
    find_jurisdiction,
    load_settings,
    setup_source,
)


def _django_cmds() -> None:
    """
    Execute Django commands to ensure database is configured correctly
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djapp.settings")
    execute_from_command_line("migrate")
    execute_from_command_line("load_divisions")


def generate_geo_data(
    SETTINGS, jurisdictions, run_migrations=False, upload_data=False
) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        os.environ.setdefault(
            "DATABASE_URL",
            "postgis://openstates:openstates@localhost:5432/openstatesorg",
        )

    """
    Download shp files from TIGER
    """
    for jur in jurisdictions:
        if jur not in JURISDICTION_NAMES:
            print(f"Invalid jurisdiction {jur}. Skipping.")
            continue
        if jur not in SETTINGS["jurisdictions"]:
            print(f"Skipping {jur}. No configuration present.")
            continue
        print(f"Fetching shapefiles for {jur}")

        jurisdiction = find_jurisdiction(jur)
        download_from_tiger(jurisdiction, "RD18", SETTINGS)
    download_boundary_file(SETTINGS["BOUNDARY_YEAR"])

    """
    Convert downloaded shp files to geojson
    """
    convert_to_geojson(SETTINGS)

    create_tiles(SETTINGS)

    if run_migrations:
        _django_cmds()

    if upload_data:
        bulk_upload(SETTINGS)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Download and process shapefiles for defined jurisdictions",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--jurisdiction",
        "-j",
        type=str,
        nargs="+",
        default=JURISDICTION_NAMES,
        help="The jurisdiction(s) to download shapefiles for",
    )
    parser.add_argument(
        "--clean-source",
        action="store_true",
        default=False,
        help="Remove any cached download/processed data",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=f"{ROOTDIR}/configs",
        help="Config directory for downloading geo data",
    )
    parser.add_argument(
        "--run-migrations",
        "-m",
        action="store_true",
        default=False,
        help="Run database migrations and uploads",
    )
    parser.add_argument(
        "--upload-data",
        "-u",
        action="store_true",
        default=False,
        help="Actually upload data to S3/Database",
    )
    args = parser.parse_args()

    setup_source(args.clean_source)
    SETTINGS = load_settings(args.config)
    generate_geo_data(
        SETTINGS, args.jurisdiction, args.run_migrations, args.upload_data
    )
