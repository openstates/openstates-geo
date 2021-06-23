# Since build time and size isn't a priority, we'll just use
# `ubuntu`, instead of `debian` or `alpine`, since
# Ubuntu's apt-get installations are simpler
FROM ubuntu:18.04

# These environment variables are required to fix a bug when
# running Mapbox CLI within CircleCI. See end of build log here:
# https://circleci.com/gh/openstates/openstates-district-maps/38
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8

# CircleCI requires a few packages for "primary containers,"
# which already come with Ubuntu, or are installed below
# https://circleci.com/docs/2.0/custom-images/#required-tools-for-primary-containers
RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	gdal-bin \
	curl \
	unzip \
	git \
	build-essential \
	libsqlite3-dev \
	zlib1g-dev
RUN git clone https://github.com/mapbox/tippecanoe.git && \
	cd tippecanoe && \
	make -j && \
	make install

ADD ./requirements.txt /opt/openstates-district-maps/requirements.txt
WORKDIR /opt/openstates-district-maps
RUN pip3 install -r requirements.txt

ADD ./make-tiles.sh /opt/openstates-district-maps/make-tiles.sh
ADD ./get-shapefiles.py /opt/openstates-district-maps/get-shapefiles.py
ADD ./join-ocd-division-ids.py /opt/openstates-district-maps/join-ocd-division-ids.py

CMD ./make-tiles.sh
