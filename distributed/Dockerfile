FROM continuumio/miniconda3

USER root
RUN  apt-get update && apt install libgl1-mesa-glx --yes

RUN mkdir /home/distributed
COPY requirements.txt home/distributed

WORKDIR /home/distributed

RUN conda config --add channels ospc
RUN conda config --add channels ospc/label/dev
RUN conda config --append channels conda-forge

RUN conda install numpy>=1.12.1 pandas>=0.23.0 taxcalc=0.20.1 \
    btax=0.2.2 ogusa=0.5.11 matplotlib numba six bokeh>=0.12.7 mock xlrd \
    sphinx nomkl

RUN pip install -r requirements.txt

RUN mkdir /home/distributed/api
WORKDIR /home/distributed/api

# not safe. don't publish with token
# see conversations like: https://github.com/moby/moby/issues/33343
ARG PUF_TOKEN
RUN if [ -z ${PUF_TOKEN+x} ]; \
        then echo PUF token not specified; \
        else echo getting and writing PUF file && \
            conda install taxpuf -c https://conda.anaconda.org/t/$PUF_TOKEN/opensourcepolicycenter && \
            write-latest-taxpuf; \
            gunzip -k puf.csv.gz; \
        fi
