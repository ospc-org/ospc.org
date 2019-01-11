FROM heroku/miniconda:3

# Grab requirements.txt.
ADD ./requirements.txt /requirements.txt
ADD ./conda-requirements.txt /conda-requirements.txt

# python version
RUN python --version

# Install dependencies
RUN conda update conda
RUN conda install -c pslmodels -c anaconda --file conda-requirements.txt --yes
RUN pip install -qr requirements.txt

# Add our code
ADD ./webapp /opt/webapp/
WORKDIR /opt

ADD ./templates /opt/templates/

ADD ./manage.py /opt/
ADD ./static /opt/static/
RUN python manage.py collectstatic --noinput

# create NewRelic file
ARG NEW_RELIC_TOKEN
RUN newrelic-admin generate-config $NEW_RELIC_TOKEN newrelic.ini
ENV NEW_RELIC_CONFIG_FILE=newrelic.ini

CMD newrelic-admin run-program gunicorn --bind 0.0.0.0:$PORT webapp.wsgi
