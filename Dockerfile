FROM python:3.9-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends -qq \
        gdal-bin \
        git \
        build-essential \
        libsqlite3-dev \
        zlib1g-dev \
    && pip3 --no-cache-dir --disable-pip-version-check install poetry \
    && git clone https://github.com/mapbox/tippecanoe.git \
    && cd tippecanoe \
    && make -j \
    && make install

ADD pyproject.toml /opt/openstates-district-maps/
ADD poetry.lock /opt/openstates-district-maps/
WORKDIR /opt/openstates-district-maps

RUN poetry install --no-dev \
    && rm -r /root/.cache/pypoetry/cache /root/.cache/pypoetry/artifacts/ \
    && apt-get remove -y -qq \
        build-essential \
        git \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -r /var/lib/apt/lists/*

ADD scripts/ /opt/openstates-district-maps/scripts/
ADD data/ /opt/openstates-district-maps/data/
ADD djapp/ /opt/openstates-district-maps/djapp/
ADD manage.py /opt/openstates-district-maps/
ADD update-tiles.sh /opt/openstates-district-maps/

CMD ["/bin/bash", "update-tiles.sh"]
