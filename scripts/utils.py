import os
from pathlib import Path
import shutil
import us

"""
two 'parent' calls to move back to directory
containing the script (scripts) and then
move up one more directory (to the git root)
"""
ROOTDIR = Path(__file__).parent.parent.absolute()

JURISDICTION_NAMES = [s.name for s in us.STATES + [us.states.PR, us.states.DC]]
JURISDICTIONS = [s for s in us.STATES + [us.states.PR, us.states.DC]]


def find_jurisdiction(jur_name: str):
    """
    Return a github.com/unitedstates/python-us style
    jurisdiction object so we can (potentially) back fill
    """
    for jurisdiction in JURISDICTIONS:
        if jur_name == jurisdiction.name:
            return jurisdiction


def setup_source(clean: bool = False):
    """
    simple function to clean up our source data
    if we're completely retrying
    """
    if clean:
        shutil.rmtree(f"{ROOTDIR}/data/", ignore_errors=True)
    os.makedirs(f"{ROOTDIR}/data/source/", exist_ok=True)
    os.makedirs(f"{ROOTDIR}/data/geojson/", exist_ok=True)
