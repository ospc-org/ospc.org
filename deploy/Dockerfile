FROM continuumio/miniconda3

MAINTAINER Henry Doupe <henry.doupe@aei.org>

LABEL "component"="Deploy" "Iteration"="test1"
USER root
RUN  apt-get update && apt install libgl1-mesa-glx --yes

RUN mkdir home/deploy
ADD ./ home/deploy

RUN conda env create -f home/deploy/fab/dropq_environment.yml
WORKDIR home/deploy
RUN /bin/bash -c "source activate aei_dropq && python setup.py develop"

WORKDIR taxbrain_server/

EXPOSE 80

# needs to be set else Celery gives an error (because docker runs commands inside container as root)
ENV C_FORCE_ROOT=1

# run supervisord
