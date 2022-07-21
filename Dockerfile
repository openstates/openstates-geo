# Since build time and size isn't a priority, we'll just use
# `ubuntu`, instead of `debian` or `alpine`, since
# Ubuntu's apt-get installations are simpler
FROM python:3.9-slim

# These environment variables are required to fix a bug when
# running Mapbox CLI within CircleCI. See end of build log here:
# https://circleci.com/gh/openstates/openstates-district-maps/38
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# CircleCI requires a few packages for "primary containers,"
# which already come with Ubuntu, or are installed below
# https://circleci.com/docs/2.0/custom-images/#required-tools-for-primary-containers
RUN apt-get update -qq \
    && apt-get install -y --no-install-recommends -qq \
	gdal-bin \
	git \
	build-essential \
	libsqlite3-dev \
	zlib1g-dev \
    && pip3 --no-cache-dir --disable-pip-version-check install poetry \
    && git clone https://github.com/mapbox/tippecanoe.git && \
	cd tippecanoe && \
	make -j && \
	make install

ADD pyproject.toml /opt/openstates-district-maps/
ADD poetry.lock /opt/openstates-district-maps/
WORKDIR /opt/openstates-district-maps
RUN poetry install --no-dev \
    && rm -r /root/.cache/pypoetry/cache /root/.cache/pypoetry/artifacts/

ADD scripts/ /opt/openstates-district-maps/scripts/
ADD data/ /opt/openstates-district-maps/data/
ADD manage.py /opt/openstates-district-maps/
ADD update-tiles.sh /opt/openstates-district-maps/

CMD ["/bin/bash", "update-tiles.sh"]
