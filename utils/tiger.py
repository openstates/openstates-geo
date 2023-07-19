import os
import zipfile
import requests
import urllib.request

from .general import (
    ROOTDIR,
    TIGER_ROOT,
)


def download_from_tiger(jurisdiction: str, prefix: str, settings: dict):
    """
    URLs are somewhat hard-coded here...
    Generally...download three files for each jurisdiction:
    1. Federal congress (cd) boundaries
    2. Upper chamber boundaries (sldu)
    3. lower chamber boundaries (sldl)
    Some jurisdictions (e.g. NE, DC) don't have all three files
    so we allow a download to fail and just log and move on
    """
    fips = jurisdiction.fips
    jur_name = settings["FIPS_NAME_MAP"].get(
        fips, jurisdiction.name.upper().replace(" ", "_")
    )
    # should end up like cd118
    session = f"cd{settings['congress_session']}"
    url_root = f"{TIGER_ROOT}/TIGER_{prefix}/STATE/{fips}_{jur_name}/{fips}"
    urls = {
        "cd": f"{url_root}/tl_rd22_{fips}_{session}.zip",
        "sldu": f"{url_root}/tl_rd22_{fips}_sldu.zip",
        "sldl": f"{url_root}/tl_rd22_{fips}_sldl.zip",
    }
    """
    remove any URLs we shouldn't download for the jurisdiction
    e.g. lower chamber in NE/DC
    """
    for k in settings["jurisdictions"][jurisdiction.name].get("ignored_chambers", []):
        urls.pop(k)
    mappings = settings["jurisdictions"][jurisdiction.name]["id-mappings"]
    for key in urls.keys():
        if "url" in mappings.get(key, {}):
            urls[key] = mappings[key]["url"]
    for url_type, url in urls.items():
        filename = url.split("/")[-1]
        fullpath = f"{ROOTDIR}/data/{filename}"
        if os.path.exists(fullpath):
            print(f"skipping {jurisdiction.name} {filename}")
            continue
        try:
            _download_and_extract(url, fullpath)
        except Exception as e:
            print(f"Couldn't download {jurisdiction.name} {filename} :: {e}")


def download_boundary_file(boundary_year: str):
    """
    Use separate download pattern because this file
    needs to be processed separately
    """
    output = f"{ROOTDIR}/data/cb_{boundary_year}_us_nation_5m.zip"
    if os.path.exists(output):
        print("Boundary file exists. Skipping download.")
        return
    url = f"{TIGER_ROOT}/GENZ{boundary_year}/shp/cb_{boundary_year}_us_nation_5m.zip"
    print(f"Downloading national boundary from {url}")
    _ = urllib.request.urlretrieve(url, output)
    with zipfile.ZipFile(output, "r") as zf:
        zf.extractall(f"{ROOTDIR}/data/boundary/")


def _download_and_extract(url: str, filename: str):
    response = requests.get(url)

    if response.status_code == 200:
        # This _could_ all be done with a single file operation,
        # by using a `BytesIO` file-like object to temporarily hold the
        # HTTP response. However, that's less readable and maintainable,
        # and a bit of delay isn't a problem given the slowness
        # of the Census downloads in the first place.
        with open(filename, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(filename, "r") as z:
            for obj in z.infolist():
                try:
                    z.extract(obj, f"{ROOTDIR}/data/source_cache/")
                except Exception as e:
                    print(f"Failed to extract {obj.filename}: {e}")
    else:
        response.raise_for_status()
