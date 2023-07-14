FROM python:3.9-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -qqy \
      gdal-bin \
      git \
      build-essential \
      libsqlite3-dev \
      zlib1g-dev
RUN pip install --disable-pip-version-check --no-cache-dir wheel \
    && pip install --disable-pip-version-check --no-cache-dir crcmod poetry
RUN git clone https://github.com/felt/tippecanoe.git && \
    cd tippecanoe && \
    make -j && \
    make install

WORKDIR /opt/openstates-district-maps
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --only=main --no-root

COPY utils utils/
COPY configs configs/
COPY djapp djapp/
COPY generate-geo-data.py .

RUN poetry install --only=main \
    && rm -r /root/.cache/pypoetry/cache /root/.cache/pypoetry/artifacts/ \
    && DEBIAN_FRONTEND=noninteractive apt-get remove -yqq build-essential libsqlite3-dev zlib1g-dev git \
    && DEBIAN_FRONTEND=noninteractive apt-get autoremove -yqq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# We use --clean-source here to ensure we don't accidentally run against messy data somehow
CMD ["poetry", "run", "python", "generate-geo-data.py", "--run-migrations", "--upload-data", "--clean-source"]
