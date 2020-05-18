FROM ubuntu:20.04

RUN true \
    && apt-get update \
    && apt-get install -y apt-utils 2>&1 | \
        grep -v "debconf: delaying package configuration, since apt-utils is not installed" \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes \
        apt-utils \
        python \
        python3-pip \
        git \
    && rm -rf /var/cache/apt/archives \
    && true

ENV BDIST_WOTMOD_PYTHON27 /usr/bin/python2

WORKDIR /build
