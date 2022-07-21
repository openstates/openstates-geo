#!/usr/bin/env bash

if ! command -v tippecanoe > /dev/null 2>&1; then
    echo "Missing local tippecanoe install...cannot run"
    exit 1
fi

set -eo pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Installing dependencies..."
poetry install

echo "Collecting shapefiles..."
poetry run python "${SCRIPT_DIR}/scripts/get-shapefiles.py"

echo "Converting to geojson files..."
poetry run python "${SCRIPT_DIR}/scripts/to-geojson.py"

echo "Loading divisions..."
poetry run "${SCRIPT_DIR}/manage.py" load_divisions

echo "Converting to mbtiles and uploading..."
poetry run "${SCRIPT_DIR}/scripts/make-tiles.py"
