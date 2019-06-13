FROM heroku/miniconda:3

# Grab requirements.txt.
ADD ./requirements.txt /requirements.txt
ADD ./conda-requirements.txt /conda-requirements.txt

# python version
RUN python --version

# Install dependencies
RUN conda update conda
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
COPY taxcalc-0.24.0-py36_0.tar.bz2 /
COPY btax-0.2.8-py36_0.tar.bz2 /
RUN conda install --yes /taxcalc-0.24.0-py36_0.tar.bz2
RUN conda install --yes /btax-0.2.8-py36_0.tar.bz2
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
