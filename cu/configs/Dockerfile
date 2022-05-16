# This is a template for the Dockerfile.
#
# This should give an idea what plain celery-utils needs to run.

FROM ubuntu:latest AS build-s0
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
                 git \
                 iproute2 \
                 jq \
                 python3-gdbm \
                 python3-pip

RUN mkdir /build_cu
RUN mkdir /code

# install celery-utils package
FROM build-s0 AS build-s1
WORKDIR /build_cu
RUN git clone -b dev https://github.com/esovetkin/celery-utils.git build; cd build; pip install -e .

# this builds the current app
FROM build-s1 AS build-s2
WORKDIR /code
ADD . /code
RUN pip3 install --upgrade -e .

# this allows running docker container as a different user
RUN git config --global --add safe.directory /code
