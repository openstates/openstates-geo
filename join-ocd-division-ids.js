#! /usr/bin/env node

const fs = require('fs')
const geojsonStream = require('geojson-stream')
const parse = require('d3-dsv').csvParse
const us = require('us')

const GEOJSON = './data/sld.geojson'
const SLDU_CSV = './data/sldu-ocdid.csv'
const SLDL_CSV = './data/sldl-ocdid.csv'
const OUTPUT = './data/sld-with-ocdid.geojson'

const sldu = parse(fs.readFileSync(SLDU_CSV, 'utf-8'))
const sldl = parse(fs.readFileSync(SLDL_CSV, 'utf-8'))

const parser = geojsonStream.parse()

const writer = fs.createWriteStream(OUTPUT)
writer.write('{ "type": "FeatureCollection", "features": [\n')

// Need to use stream processing, since the filesize of all the
// SLD files combined is far beyond Node's memory limits
let isFirstFile = true
fs.createReadStream(GEOJSON)
  .pipe(parser)
  .on('data', f => {
    const type = f.properties.MTFCC === 'G5210' ? 'sldu' : 'sldl'

    // Identify the OCD ID by making a lookup against the CSV files
    // The OCD ID is the cannonical identifier of an area on
    // the Open States platform
    const geoid = `${type}-${f.properties.GEOID}`
    const slduId = sldu.find(d => d.census_geoid_14 === geoid)
    const sldlId = sldl.find(d => d.census_geoid_14 === geoid)
    const ocdid = (slduId && slduId.id) ||
      (sldlId && sldlId.id) ||
      null

    // Although OCD IDs contain the state postal code, psarsing
    // an ID to determine structured data is bad practice,
    // so add a standalone state postal abbreviation property too
    const state = us.STATES_AND_TERRITORIES.find(
      s => s.fips === f.properties.STATEFP
    ).abbr.toLowerCase()

    // The source shapefiles have a large number of properties,
    // but the output tiles only need these three for their
    // use on openstates.org; this helps keep down the MBTiles
    // file size
    f.properties = { ocdid, type, state }

    if (isFirstFile) {
      isFirstFile = false
    } else {
      writer.write(',\n')
    }

    writer.write(JSON.stringify(f))
  })
  .on('end', () => {
    writer.end(']}')
  })
