#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import django
from django.core.management import call_command
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
    upload_tiles,
    print_script_progress,
)


def _django_cmds() -> None:
    """
    Execute Django commands to ensure database is configured correctly
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djapp.settings")
    django.setup()
    call_command("migrate")
    call_command("load_divisions")
    call_command("clean_divisions")


def generate_geo_data(
    SETTINGS,
    jurisdictions,
) -> None:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        os.environ.setdefault(
            "DATABASE_URL",
            "postgis://openstates:openstates@localhost:5405/openstatesorg",
        )

    """
    Download shp files from TIGER
    """
    print_script_progress("Download shp files from TIGER")
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
    print_script_progress("Download boundary file")
    download_boundary_file(SETTINGS["BOUNDARY_YEAR"])

    """
    Convert downloaded shp files to geojson
    """
    print_script_progress("Convert downloaded shp files to geojson")
    convert_to_geojson(SETTINGS)

    if SETTINGS["create_tiles"]:
        print_script_progress("Create tiles")
        create_tiles(SETTINGS)

    if SETTINGS["run_migrations"]:
        print_script_progress("Run migrations")
        _django_cmds()

    if SETTINGS["upload_data"]:
        print_script_progress("Upload data")
        bulk_upload(SETTINGS)
        upload_tiles()


def main():
    parser = ArgumentParser(
        description="Download and process shapefiles for defined jurisdictions",
        formatter_class=ArgumentDefaultsHelpFormatter,
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
        help="Actually upload data to S3/Mapbox",
    )
    parser.add_argument(
        "--skip-tile-creation",
        "-s",
        action="store_true",
        default=False,
        help="Don't generate Mapbox tilesets",
    )
    args = parser.parse_args()
    SETTINGS = load_settings(
        args.config,
        args.run_migrations,
        args.upload_data,
        args.skip_tile_creation,
        args.clean_source,
    )
    setup_source(SETTINGS)

    generate_geo_data(
        SETTINGS,
        JURISDICTION_NAMES,
    )


if __name__ == "__main__":
    main()
