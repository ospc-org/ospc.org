FROM continuumio/miniconda

MAINTAINER Henry Doupe <henry.doupe@aei.org>

LABEL "component"="Deploy"
USER root
RUN  apt-get update && apt install libgl1-mesa-glx --yes

RUN mkdir home/deploy
ADD ./ home/deploy

WORKDIR home/deploy

RUN conda config --add channels ospc
RUN conda config --add channels ospc/label/dev
RUN conda config --append channels conda-forge

RUN conda install python=2.7.14 numpy>=1.12.1 pandas>=0.22.0 taxcalc=0.15.2 \
    btax=0.2.2 ogusa=0.5.8 matplotlib numba six bokeh=0.12.7 mock xlrd \
    sphinx nomkl

RUN pip install -r requirements.txt

RUN python setup.py develop

WORKDIR taxbrain_server/
