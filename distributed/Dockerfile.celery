ARG TAG
FROM distributed:$TAG

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

COPY ./api /home/distributed/api
COPY ./setup.py /home/distributed
RUN cd /home/distributed && pip install -e .

ENTRYPOINT celery -A celery_tasks worker --loglevel=info --concurrency=1
