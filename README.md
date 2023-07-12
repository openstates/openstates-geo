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
- [tippecanoe](https://github.com/felt/tippecanoe)

## Ensuring The Right Shape Files

We download our shapefiles from [census.gov](https://www2.census.gov/geo/tiger).

The organization of files within TIGER's site means that we may have to change the layout of downloaded files from year to year (in `utils/tiger.py`). As long as we consistently add proper files into `data/source_cache` for the rest of the scripts to process, changing the initial download location shouldn't matter.

See Appendix A below on Geographic Data Sources for more context.

You'll probably want to remove any cached files in `./data/`. The download tool may try to re-use cached files from the wrong year if they still exist. (We don't manually remove these files because you may need to re-run the scripts, and skipping downloads is useful)

### Note on file naming

You'll see many files with names like `sldu`, `sldl` or `cd` during this process. Here is a quick layout of what those file name abbreviations mean:

- `sldu`
  - State Level District Upper -> Upper Chamber District boundaries
- `sldl`
  - State Level District Lower -> Lower Chamber District boundaries
- `cd`
  - Congressional District -> Federal Congressional District boundaries

We do not collect boundaries for Federal Senate because each state has the same number of senators and they are considered "at-large" (having no district boundaries beyond the entire state).

## Running

There are several steps, which typically need to be run in order:

1) Setup Poetry:

  - `poetry install`

2 ) Make sure `DATABASE_URL` is set correctly in the environment (pointing at either the `geo` database in production or to a local copy, e.g. `DATABASE_URL=postgis:/<user>:<password>@<db_host>/geo`)

3) Download and format geo data:

  - `poetry run python generate-geo-data.py`
    - Note that this script does not fail on individual download failures. If you see failures in the run, make sure they are expected (e.g. NE/DC lower should fail)

4) Currently, we have to manually upload the resulting tilesets to [Mapbox Studio](https://studio.mapbox.com/tilesets/).

  - We'll need to upload `data/sld.mbtiles` and `data/cd.mbtiles`.

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

#### TIGER SLDL

[2022](https://www2.census.gov/geo/tiger/TIGER2022/SLDL/)

This contains data, including shapefiles, about State Legislative Districts in Lower chambers (SLDL).

#### TIGER SLDU

[2022](https://www2.census.gov/geo/tiger/TIGER2022/SLDU/)

This contains data, including shapefiles, about State Legislative Districts in Upper chambers (SLDU).

#### TIGER CD

[2022](https://www2.census.gov/geo/tiger/TIGER2022/CD/)

This contains data, including shapefiles, about Congressional Districts.

