# Issues

- Tracked in our central issue repository: [Geo Issues](https://github.com/openstates/issues/labels/component%3Ageo)

# Open States Geography Processing & Server

Generate and upload map tiles for the state-level legislative district maps on [openstates.org](https://openstates.org/), both for [state overviews](https://openstates.org/ca/) and for [individual legislators](https://openstates.org/person/tim-ashe-4mV4UFZqI2WsxsnYXLM8Vb/).

- Source: SLDL and SLDU shapefiles from [the Census's TIGER/Line database](https://www.census.gov/geo/maps-data/data/tiger-line.html)
- Output: a single nationwide MBTiles vector tile set, uploaded to Mapbox for hosting
    - Intermediate files are also built and retained locally, stored in the `data` directory for debugging

![](tileset-screenshot.png)

## Dependencies

- Python 3 and `poetry`
- GDAL 2
    - in particular, the `ogr2ogr` binary
- `tippecanoe`

### GDAL

#### Linux

The GDAL packages vary by distribution, but generally:

- rpm -> `gdal`
- deb -> `gdal-bin`

### Installing tippecanoe

[Tippecanoe](https://github.com/mapbox/tippecanoe.git) is a tool maintained by Mapbox that helps us convert different shape files into a consistent format.

#### Linux

```bash
git clone https://github.com/mapbox/tippecanoe.git
cd tippecanoe
make -j
sudo make install
```

#### OS X

```bash
brew install tippecanoe
```

## Running

There are several steps, which typically need to be run in order:

1. Set up environment variables
    - MAPBOX_ACCOUNT
        - OPTIONAL (if left blank, upload step will be skipped)
    - MAPBOX_TOKEN
        - OPTIONAL (if left blank, upload step will be skipped)
    - DATABASE_URL
        - To a working postgis instance (if using docker, the default will work)

2. Setup Poetry:

    `poetry install`

3. Download SLD shapefiles:

    `poetry run python scripts/get-shapefiles.py`

4. Convert to geojson with division IDs:

    `poetry run python scripts/to-geojson.py`

5. Import into database:

    `poetry run python manage.py load_divisions`

6. Convert to mbtiles and upload:

    `poetry run python scripts/make-tiles.py`

The `MAPBOX_ACCOUNT` name and `MAPBOX_ACCESS_TOKEN` (with upload privileges) must be set as environment variables. If not, then the upload step will be skipped.

These steps are collected in `update-tiles.sh` for convenience.

### Running within Docker

Instead of setting up your local environment you can instead run using Docker. Using Docker Compose will still allow you to access all intermediate files from the processing, within your local `data` directory.

Build and run with Docker Compose. Similar to running without Docker, the `MAPBOX_ACCOUNT` and `MAPBOX_ACCESS_TOKEN` must be set in your local environment.

```
docker-compose up
```
