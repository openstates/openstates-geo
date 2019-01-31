# Since build time and size isn't a priority, we'll just use
# ubuntu, instead of debian or alpine
FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	nodejs \
	npm \
	gdal-bin \
	curl \
	gawk \
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
ADD ./package.json /opt/openstates-district-maps/package.json
WORKDIR /opt/openstates-district-maps

RUN pip3 install -r requirements.txt
RUN npm install

ADD ./get-all-sld-shapefiles.py /opt/openstates-district-maps/get-all-sld-shapefiles.py
ADD ./join-ocd-division-ids.js /opt/openstates-district-maps/join-ocd-division-ids.js
ADD ./make-tiles.sh /opt/openstates-district-maps/make-tiles.sh

CMD ./make-tiles.sh
