ARG TAG
FROM distributed:$TAG

LABEL build="flask" date="2018-06-13"

USER root

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

ENV HOST 0.0.0.0
ENV PORT 5050
ENV DEBUG true

# expose the app port
EXPOSE 80
EXPOSE 5050

COPY ./api /home/distributed/api
COPY ./setup.py /home/distributed
RUN cd /home/distributed && pip install -e .

# run the app server
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "api:create_app()", "--access-logfile", "-"]
