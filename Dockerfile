# Since build time and size isn't a priority, we'll just use
# `ubuntu`, instead of `debian` or `alpine`, since
# Ubuntu's apt-get installations are simpler
FROM python:3.10-slim

# These environment variables are required to fix a bug when
# running Mapbox CLI within CircleCI. See end of build log here:
# https://circleci.com/gh/openstates/openstates-district-maps/38
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# CircleCI requires a few packages for "primary containers,"
# which already come with Ubuntu, or are installed below
# https://circleci.com/docs/2.0/custom-images/#required-tools-for-primary-containers
RUN apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -qqy \
      gdal-bin \
      git \
      build-essential \
      libsqlite3-dev \
      zlib1g-dev \
    && pip install --disable-pip-version-check --no-cache-dir -q crcmod wheel poetry
RUN git clone https://github.com/mapbox/tippecanoe.git && \
    cd tippecanoe && \
    make -j && \
    make install

WORKDIR /opt/openstates-district-maps
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --only=main \
    && rm -r /root/.cache/pypoetry/cache /root/.cache/pypoetry/artifacts/

COPY scripts .
COPY manage.py .
COPY make-tiles.sh .
COPY djapp .

CMD ["bash", "/opt/openstates-district-maps/make-tiles.sh"]
