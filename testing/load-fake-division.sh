#!/usr/bin/env bash

SCRIPT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
PGPASSWORD=openstates
export PGPASSWORD

# get geometry of a division
psql -t -P pager=off -h localhost -p 5405 -U openstates openstatesorg -c "SELECT shape FROM geo_division WHERE id='ocd-division/country:us/state:al/sldl:100'" | tr -d ' ' > "${SCRIPT_DIR}/divisiondata"

psql -t -P pager=off -h localhost -p 5405 -U openstates openstatesorg -c "INSERT INTO geo_division (id, name, shape, division_set_id, state) VALUES ('ocd-division/country:us/state:al/sldl:111', '111', '$(cat "${SCRIPT_DIR}/divisiondata")', 'sldl', 'AL')"

rm -f "${SCRIPT_DIR}/divisiondata"
