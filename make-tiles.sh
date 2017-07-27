#!/usr/bin/env bash

python get-all-sld-shapefiles.py

for f in ./data/*.zip; do
	unzip -o -d ./data "$f"
done

for f in ./data/*.shp; do
	ogr2ogr -f GeoJSON "${f}.geojson" "$f"
done

echo '{ "type": "FeatureCollection", "features": [' > ./data/sld.geojson
cat ./data/tl_2016_*.geojson >> ./data/sld.geojson
sed -i '' '/^{$/d' ./data/sld.geojson
sed -i '' '/^}$/d' ./data/sld.geojson
sed -i '' '/^"type": "FeatureCollection",$/d' ./data/sld.geojson
sed -i '' '/^"features": \[$/d' ./data/sld.geojson
sed -i '' '/^\]$/d' ./data/sld.geojson
# Now, all lines are GeoJSON Feature objects
# Make sure all of them have trailing commas, except for the last
sed -i '' 's/,$//g' ./data/sld.geojson
sed -i '' 's/}$/},/g' ./data/sld.geojson
# Strip empty lines
# The macOS sed `/d` is failing to do this
awk 'NF' ./data/sld.geojson > ./data/tmp.txt
mv ./data/tmp.txt ./data/sld.geojson
echo ']}' >> ./data/sld.geojson

tippecanoe \
	--layer sld \
	--minimum-zoom 2 --maximum-zoom 13 \
	--include GEOID --include LSAD \
	--detect-shared-borders \
	--simplification 10 \
	--force --output ./data/sld.mbtiles \
	./data/sld.geojson
