#! /usr/bin/env python

import requests
import us


# The Census URLs are case-sensitive, oddly
URL = 'https://www2.census.gov/geo/tiger/TIGER2016/SLD{chamber_uppercase}/tl_2016_{fips}_sld{chamber}.zip'
for state in us.STATES:
	print("Fetching shapefiles for {}".format(state.name))
	for chamber in ['l', 'u']:
		fips = state.fips
		download_url = URL.format(fips=fips, chamber=chamber, chamber_uppercase=chamber.upper())
		data = requests.get(download_url).content
		with open('./data/tl_2016_{fips}_sld{chamber}.zip'.format(fips=fips, chamber=chamber), 'wb') as f:
			f.write(data)
