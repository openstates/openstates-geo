import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor


DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "openstates")
DB_NAME = os.environ.get("DB_NAME", "newgeo")
conn = psycopg2.connect(
    f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' port='{DB_PORT}' password='{DB_PASSWORD}'"
)


def response(body, status_code=200):
    return {
        "statusCode": 200,
        "body": json.dumps(body),
        "headers": {"Content-Type": "application/json"},
    }


def geo_query(lat, lon):
    cur = conn.cursor(cursor_factory=RealDictCursor)

    GEO_QUERY = """SELECT id, name FROM geo_division
    WHERE ST_Contains(shape, 'POINT(%s %s)'::geography::geometry);"""

    cur.execute(GEO_QUERY, [lat, lon])
    return cur.fetchall()


def lambda_handler(event, context):
    error = None
    params = event.get("queryStringParameters", {})
    try:
        lat = float(params["lat"])
        lng = float(params["lng"])
    except KeyError:
        error = "Must provide lat & lng parameters."
    except ValueError:
        error = "Invalid lat, lng parameters."

    if error:
        return response({"error": error}, 400)

    divisions = geo_query(lng, lat)
    return response({"divisions": divisions})


if __name__ == "__main__":
    import pprint

    pprint.pprint(
        lambda_handler({"queryStringParameters": {"lat": 38.9, "lng": -77}}, None)
    )
