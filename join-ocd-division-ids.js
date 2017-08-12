#! /usr/bin/env node

const fs = require('fs')
const geojsonStream = require('geojson-stream')
const parse = require('d3-dsv').csvParse

const GEOJSON = './data/sld.geojson'
const SLDL_CSV = './data/sldl-ocd-ids.csv'
const SLDU_CSV = './data/sldu-ocd-ids.csv'
const OUTPUT = './data/sld-with-ocdid.geojson'

const sldl = parse(fs.readFileSync(SLDL_CSV, 'utf-8'))
const sldu = parse(fs.readFileSync(SLDU_CSV, 'utf-8'))

const parser = geojsonStream.parse()

const writer = fs.createWriteStream(OUTPUT)
writer.write('{ "type": "FeatureCollection", "features": [\n')

// Need to stream, since the filesize of the combined
// SLDs is too large for Node's maximum memory
let first = true
fs.createReadStream(GEOJSON)
  .pipe(parser)
  .on('data', f => {
    // Remove water-only placeholder districts
    if (f.properties.GEOID.endsWith('ZZZ')) { return }

    const chamber = f.properties.LSAD.slice(1, 2).toLowerCase()
    const geoid = `sld${chamber}-${f.properties.GEOID}`

    const slduId = sldu.find(d => d.census_geoid_14 === geoid)
    const sldlId = sldl.find(d => d.census_geoid_14 === geoid)
    const ocdid = slduId ? slduId.id :
      sldlId ? sldlId.id :
      null
    f.properties = { ocdid }

    if (first) {
      first = false
    } else {
      writer.write('\n,\n')
    }
    writer.write(JSON.stringify(f))
  })
  .on('end', () => {
    writer.end(']}')
  })
