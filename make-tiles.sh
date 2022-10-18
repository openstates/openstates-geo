#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
pushd "${SCRIPT_DIR}/"

###
# Following README instructions
###
poetry run python scripts/get-shapefiles.py
poetry run python scripts/to-geojson.py
poetry run python manage.py migrate
poetry run python manage.py load_divisions
poetry run python scripts/make-tiles.py
