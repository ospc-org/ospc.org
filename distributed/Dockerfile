FROM continuumio/miniconda3

USER root
RUN  apt-get update && apt install libgl1-mesa-glx --yes

RUN mkdir /home/distributed
COPY requirements.txt home/distributed

WORKDIR /home/distributed

RUN conda update conda
RUN conda config --add channels pslmodels
RUN conda config --append channels conda-forge

# RUN conda install -c ospc -c anaconda --file conda-requirements.txt --yes
RUN conda install --yes \
    "numpy==1.14.2" \
    "pandas==0.23.4" \
    "bokeh==1.0.2" \
    "numba==0.41.0" \
    "scipy==1.1.0" \
    "pyparsing==2.3.0" \
    "matplotlib==3.0.1" \
    "pillow==5.3.0"
COPY taxcalc-0.24.0-py36_0.tar.bz2 /home/taxcalc-0.24.0-py36_0.tar.bz2
COPY btax-0.2.8-py36_0.tar.bz2 /home/btax-0.2.8-py36_0.tar.bz2
RUN ls /
RUN conda install --yes /home/taxcalc-0.24.0-py36_0.tar.bz2
RUN conda install --yes /home/btax-0.2.8-py36_0.tar.bz2

RUN pip install -r requirements.txt

RUN mkdir /home/distributed/api
WORKDIR /home/distributed/api

# not safe. don't publish with token
# see conversations like: https://github.com/moby/moby/issues/33343
ARG PUF_TOKEN
RUN if [ -z ${PUF_TOKEN+x} ]; \
        then echo PUF token not specified; \
        else echo getting and writing PUF file && \
            conda install taxpuf matplotlib>=3.0.1 -c https://conda.anaconda.org/t/$PUF_TOKEN/opensourcepolicycenter && \
            write-latest-taxpuf && \
            gunzip -k puf.csv.gz; \
        fi

WORKDIR /home/distributed

RUN pip install -r requirements.txt

WORKDIR /home/distributed/api
