#!/usr/bin/env bash

set -e

mkdir -p data

echo "Downloading TIGER/Line shapefiles"
./get-all-sld-shapefiles.py

echo "Additional shapefiles, such as New Hampshire floterials and DC at-large, should be downloaded here in the future"

echo "Unzip the shapefiles"
for f in ./data/*.zip; do
	# Catch cases where the ZIP file doesn't function, like DC SLDL;
	# this prevents the `unzip` and `ogr2ogr` from easily
	# coexisting within the same `for` loop
	unzip -q -o -d ./data "$f" || echo "Failed to unzip $f; this is probably a non-existant chamber"
done

echo "Convert to GeoJSON and clip boundaries to shorelines"
# Prepare the national boundary, to use to clip boundaries to
# the coastline and Great Lakes
curl --silent --output ./data/cb_2017_us_nation_5m.zip https://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_us_nation_5m.zip
unzip -q -o -d ./data ./data/cb_2017_us_nation_5m.zip

count=0
total="$(find ./data/tl_*.shp | wc -l | xargs)"
if (( total != 102 )); then
	echo "Found an incorrect number of shapefiles ($total instead of 102)" 1>&2
	exit 1
fi
for f in ./data/tl_*.shp; do
	# OGR's GeoJSON driver cannot overwrite files, so make sure
	# the file doesn't already exist
	rm -f "${f}.geojson"

	# Water-only placeholder areas end in `ZZZ`
	ogr2ogr \
		-clipsrc ./data/cb_2017_us_nation_5m.shp \
		-where "GEOID NOT LIKE '%ZZZ'" \
		-f GeoJSON \
		"${f}.geojson" \
		"$f"

	((++count))
	echo -e "    ${count} of ${total} shapefiles clipped and converted"
done

echo "Concatenate the shapefiles into one file"
# This should be the purview of `@mapbox/geojson-merge`,
# but that tool isn't working properly on this volume of files
echo '{ "type": "FeatureCollection", "features": [' > ./data/sld.geojson
cat ./data/tl_*.geojson >> ./data/sld.geojson
# Remove unnecessary lines coming in from each GeoJSON file
sed -i'.bak' -e '/^{$/d' ./data/sld.geojson
sed -i'.bak' -e '/^}$/d' ./data/sld.geojson
sed -i'.bak' -e '/^"type": "FeatureCollection",$/d' ./data/sld.geojson
sed -i'.bak' -e '/^"name": .*$/d' ./data/sld.geojson
sed -i'.bak' -e '/^"crs": .*$/d' ./data/sld.geojson
sed -i'.bak' -e '/^"features": \[$/d' ./data/sld.geojson
sed -i'.bak' -e '/^\]$/d' ./data/sld.geojson
# Now, all lines besides the first are GeoJSON Feature objects
# Make sure all of them have trailing commas, except for the last
sed -i'.bak' -e 's/}$/},/g' ./data/sld.geojson
# Strip empty lines
# The macOS Homebrew sed `/d` fails to do this, and it doesn't hurt on
# other *nix platforms
gawk 'NF' ./data/sld.geojson > ./data/tmp.txt
mv ./data/tmp.txt ./data/sld.geojson
echo ']}' >> ./data/sld.geojson

echo "Join the OCD division IDs to the GeoJSON"
curl --silent --output ./data/sldu-ocdid.csv https://raw.githubusercontent.com/opencivicdata/ocd-division-ids/master/identifiers/country-us/census_autogenerated_14/us_sldu.csv
curl --silent --output ./data/sldl-ocdid.csv https://raw.githubusercontent.com/opencivicdata/ocd-division-ids/master/identifiers/country-us/census_autogenerated_14/us_sldl.csv
./join-ocd-division-ids.js

echo "Convert the GeoJSON into MBTiles for serving"
tippecanoe \
	--layer sld \
	--minimum-zoom 2 --maximum-zoom 13 \
	--detect-shared-borders \
	--simplification 10 \
	--force --output ./data/sld.mbtiles \
	./data/sld-with-ocdid.geojson

if [ -z ${MAPBOX_ACCOUNT+x} ] || [ -z ${MAPBOX_ACCESS_TOKEN+x} ] ; then
	echo "Skipping upload step; MAPBOX_ACCOUNT and/or MAPBOX_ACCESS_TOKEN not set in environment"
else
	echo "Upload the MBTiles to Mapbox, for serving"
	mapbox upload "${MAPBOX_ACCOUNT}.sld" ./data/sld.mbtiles
fi
