import glob
import os
from pathlib import Path
import shutil
from openstates.metadata.data import STATES_AND_DC_PR as JURISDICTIONS
import yaml

"""
two 'parent' calls to move back to directory
containing the script (scripts) and then
move up one more directory (to the git root)
"""
ROOTDIR = Path(__file__).parent.parent.absolute()
TIGER_ROOT = "https://www2.census.gov/geo/tiger"
JURISDICTION_NAMES = [s.name for s in JURISDICTIONS]


def find_jurisdiction(jur_name: str):
    """
    Return a github.com/unitedstates/python-us style
    jurisdiction object so we can (potentially) back fill
    """
    for jurisdiction in JURISDICTIONS:
        if jur_name == jurisdiction.name:
            return jurisdiction


def setup_source(clean: bool = False, upload_data: bool = False) -> None:
    """
    simple function to clean up our source data
    if we're completely retrying
    """
    for cmd in ["tippecanoe", "ogr2ogr"]:
        if not shutil.which(cmd):
            print(f"Cannot find {cmd} in PATH. Cannot continue.")
            exit(1)

    if upload_data:
        token = os.environ.get("MAPBOX_ACCESS_TOKEN")
        if not token:
            raise Exception("Trying to upload data without MAPBOX_ACCESS_TOKEN set")
        access_id = os.environ.get("AWS_ACCESS_KEY_ID")
        if not access_id:
            raise Exception("Trying to upload data without AWS_ACCESS_KEY_ID set")
        access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        if not access_key:
            raise Exception("Trying to upload data without AWS_SECRET_ACCESS_KEY set")
    if clean:
        shutil.rmtree(f"{ROOTDIR}/data/", ignore_errors=True)
    os.makedirs(f"{ROOTDIR}/data/source_cache/", exist_ok=True)
    os.makedirs(f"{ROOTDIR}/data/geojson/", exist_ok=True)
    os.makedirs(f"{ROOTDIR}/data/boundary/", exist_ok=True)


def load_settings(
    config_dir: str, run_migrations: bool, upload_data: bool, skip_tile_creation: bool
) -> dict:
    """
    Load all yaml files (settings) recursively from the defined config_dir
    """
    with open(f"{config_dir}/settings.yml", "r") as f_in:
        settings = yaml.safe_load(f_in.read())
    settings["jurisdictions"] = dict()
    for file in glob.glob(f"{config_dir}/jurisdictions/*.yml"):
        with open(file, "r") as f:
            jur_settings = yaml.safe_load(f.read())
            settings["jurisdictions"][jur_settings["name"]] = dict(jur_settings)
    settings["run_migrations"] = run_migrations
    settings["upload_data"] = upload_data
    settings["create_tiles"] = not skip_tile_creation
    settings["aws_user"] = os.environ.get("AWS_ACCESS_KEY_ID")
    os.environ.pop("AWS_ACCESS_KEY_ID", None)
    settings["aws_password"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
    return settings
