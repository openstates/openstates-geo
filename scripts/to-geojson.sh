#!/bin/bash 

set -e

# Occasionally, the TIGER/Line website may not have properly
# served all the files, in which case the process should error
# out noisily and be re-tried
total="$(find ./data/tl_*.shp | wc -l | xargs)"
if (( total != 102 )); then
	echo "Found an incorrect number of shapefiles (${total} instead of 102)" 1>&2
	exit 1
fi

echo "Download the national boundary for clipping"
curl --silent --output ./data/cb_2017_us_nation_5m.zip https://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_us_nation_5m.zip
unzip -q -o -d ./data ./data/cb_2017_us_nation_5m.zip

echo "Convert to GeoJSON, clip boundaries to shoreline"
count=0
for f in ./data/tl_*.shp; do
	# OGR's GeoJSON driver cannot overwrite files, so make sure
	# to clear the output GeoJSONs from previous runs
	# The `{f%.*}` syntax removes the extension of the filename
	rm -f "${f%.*}.geojson"

	# Water-only placeholder "districts" end in `ZZZ`
	# Also, convert to the spatial projection (CRS:84, equivalent
	# to EPSG:4326) that is expected by tippecanoe
	ogr2ogr \
		-clipsrc ./data/cb_2017_us_nation_5m.shp \
		-where "GEOID NOT LIKE '%ZZZ'" \
		-t_srs crs:84 \
		-f GeoJSON \
		"${f%.*}.geojson" \
		"$f"
	((++count))
	echo -e "${count} of ${total} shapefiles processed"
done
