#!/bin/bash

if [[ -z "${DATABASE_URL}" ]]; then
    echo "Missing required environment variable DATABASE_URL"
    exit 2
fi
set -eou pipefail
export DATABASE_URL

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

###
# Following README instructions
###
poetry run python "${SCRIPT_DIR}/scripts/get-shapefiles.py"
poetry run python "${SCRIPT_DIR}/scripts/to-geojson.py"
poetry run python "${SCRIPT_DIR}/manage.py" migrate
poetry run python "${SCRIPT_DIR}/manage.py" load_divisions
poetry run python "${SCRIPT_DIR}/scripts/bulk-boundary-files-upload.py"
poetry run python "${SCRIPT_DIR}/scripts/make-tiles.py"
