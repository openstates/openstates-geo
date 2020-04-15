#!/usr/bin/env bash

set -e

echo "Combine all GeoJSON files into a MBTiles file for serving"
tippecanoe \
	--layer sld \
	--minimum-zoom 2 --maximum-zoom 13 \
	--detect-shared-borders \
	--simplification 10 \
	--force --output ./sld.mbtiles \
	./final-geojson/*.geojson

if [ -z ${MAPBOX_ACCOUNT+x} ] || [ -z ${MAPBOX_ACCESS_TOKEN+x} ] ; then
	echo "Skipping upload step; MAPBOX_ACCOUNT and/or MAPBOX_ACCESS_TOKEN not set in environment"
else
	echo "Upload the MBTiles to Mapbox, for serving"
	mapbox upload "${MAPBOX_ACCOUNT}.sld" ./sld.mbtiles
fi
