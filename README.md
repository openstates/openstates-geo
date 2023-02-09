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
- `tippecanoe`

## Ensuring The Right Shape Files

We download our shapefiles from [census.gov](https://www2.census.gov/geo/tiger).

The organization of files within TIGER's site means that we may have to change the layout of downloaded files from year to year (in `scripts/get-shapefiles.py`). As long as we consistently add proper files into `data/source_cache` for the rest of the scripts to process, changing the initial download location shouldn't matter.

See Appendix A below on Geographic Data Sources for more context.

You'll probably want to remove any cached files in `./data/`. The download tool may try to re-use cached files from the wrong year if they still exist. (We don't manually remove these files because you may need to re-run the scripts, and skipping downloads is useful)

## Running

There are several steps, which typically need to be run in order:

1) Setup Poetry:

  `poetry install`

2) Download SLD shapefiles:

  `poetry run ./scripts/get-shapefiles.py`

3) Convert to geojson with division IDs:

  `poetry run ./scripts/to-geojson.py`

4) Make sure `DATABASE_URL` is set to local database in `djapp/geo/settings.py`


5) Migrate database to add needed tables:

  `poetry run ./manage.py migrate`

6) Import into database:

  `poetry run ./manage.py load_divisions`

7) Convert to mbtiles and upload:

  `./scripts/make-tiles.py`

8) Currently, we have to manually upload the resulting tilesets to [Mapbox](https://studio.mapbox.com/tilesets/). We'll need to upload `data/sld.mbtiles` and `data/cd.mbtiles`.

9) Create district boundary files and upload to S3

  `poetry run python scripts/upload-bulk-boundary-files.py`

### Running within Docker

Instead of setting up your local environment you can instead run using Docker. Using Docker Compose will still allow you to access all intermediate files from the processing, within your local `data` directory.

Build and run with Docker Compose. Similar to running without Docker, the `MAPBOX_ACCOUNT` and `MAPBOX_ACCESS_TOKEN` must be set in your local environment.

```
docker-compose up make-tiles
```

# Appendix A: Geo Data Sources used by openstates-geo

openstates-geo works with shapefiles. Shapefiles can be opened by a tool called [qgis](https://www.qgis.org/en/site/)
For example, to inspect a source shapefile, such as `tl_2022_01_sldl.shp`, open up qgis and navigate to the folder where
that file resides. Open the file, it should appear in the main pane as a map. Use the "Select Features by Area or single click"
button in the toolbar, and then select a district. Metadata should appear in the right pane.

## US Census


### Redistricting

"We hold the districts used for the 2018 election until we collect the postcensal congressional and state legislative district plans
for the 118th Congress and year 2022 state legislatures" [US Census CD/SLD note](https://www.census.gov/programs-surveys/geography/technical-documentation/user-note/cd-sld-note.html)

### US Census: TIGER

Files in the TIGER data source are organized according to
[Federal Information Processing System (FIPS)](https://transition.fcc.gov/oet/info/maps/census/fips/fips.txt) codes.
Each numeric code corresponds to a US state (or other levels). For example `01` represents Alabama.

As of 12/30/22 the [TIGER page states](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html):
"All legal boundaries and names are as of January 1, 2022. Released September 30, 2022." So it seems like post-redistricting
shapefiles are not available.

#### TIGER SLDL

[2022](https://www2.census.gov/geo/tiger/TIGER2022/SLDL/)

This contains data, including shapefiles, about State Legislative Districts in Lower chambers (SLDL).

#### TIGER SLDU

[2022](https://www2.census.gov/geo/tiger/TIGER2022/SLDU/)

This contains data, including shapefiles, about State Legislative Districts in Upper chambers (SLDU).

#### TIGER CD

[2022](https://www2.census.gov/geo/tiger/TIGER2022/CD/)

This contains data, including shapefiles, about Congressional Districts.

