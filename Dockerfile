FROM debian:latest
MAINTAINER Miles Watkins <miles@openstates.org>

ARG DEBIAN_FRONTEND=noninteractive

ADD . /opt/openstates/openstates-district-maps
WORKDIR /opt/openstates/openstates-district-maps

RUN apt-get update && apt-get install -y \
	python \
	python-pip \
	nodejs \
	curl \
	unzip \
	gdal-bin \
	git \
	build-essential \
	libsqlite3-dev \
	zlib1g-dev
RUN pip install -r requirements.txt
RUN git clone https://github.com/mapbox/tippecanoe.git && \
	cd tippecanoe && make && make install && cd ..
RUN git clone https://github.com/mapbox/geojson-merge.git

CMD ./make-tiles.sh
