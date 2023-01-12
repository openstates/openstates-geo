#!/bin/bash

set -eou pipefail

if [[ -n "${DATABASE_URL}" ]]; then
    export DATABASE_URL
fi
# if [[ -n "${MAPBOX_ACCOUNT}" ]]; then
#     export MAPBOX_ACCOUNT
# fi
# if [[ -n "${MAPBOX_ACCESS_TOKEN}" ]]; then
#     export MAPBOX_ACCESS_TOKEN
# fi

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

###
# Following README instructions
###
# poetry run python "${SCRIPT_DIR}/scripts/get-shapefiles.py"
poetry run python "${SCRIPT_DIR}/scripts/to-geojson.py"
poetry run python "${SCRIPT_DIR}/scripts/make-tiles.py"
poetry run python "${SCRIPT_DIR}/manage.py" migrate
poetry run python "${SCRIPT_DIR}/manage.py" load_divisions
poetry run python "${SCRIPT_DIR}/scripts/update-boundaries.py"
