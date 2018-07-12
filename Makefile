OSPC_ANACONDA_TOKEN := `cat ~/.ospc_anaconda_token`
NEW_RELIC_TOKEN := `cat ~/.newrelic-$(VERSION)`

dist-build:
	cd distributed && \
	docker build -t opensourcepolicycenter/distributed:$(TAG) ./ --build-arg PUF_TOKEN=$(OSPC_ANACONDA_TOKEN) && \
	docker build --no-cache --build-arg TAG=$(TAG) -t opensourcepolicycenter/flask:$(TAG) --file Dockerfile.flask ./ && \
	docker build --no-cache --build-arg TAG=$(TAG) -t opensourcepolicycenter/celery:$(TAG) --file Dockerfile.celery ./

dist-push:
	cd distributed && \
	docker push opensourcepolicycenter/distributed:$(TAG) && \
	docker push opensourcepolicycenter/flask:$(TAG) && \
	docker push opensourcepolicycenter/celery:$(TAG)

dist-test:
	cd distributed && \
	docker-compose rm -f && \
	docker-compose run flask py.test -s -v && \
	docker-compose rm -f

webapp-build:
	docker build --build-arg NEW_RELIC_TOKEN=$(NEW_RELIC_TOKEN) -t opensourcepolicycenter/web:$(TAG) ./

webapp-push:
	docker push opensourcepolicycenter/web:$(TAG)

webapp-release:
	docker tag opensourcepolicycenter/web:$(TAG) registry.heroku.com/ospc-$(MODE)/web
	docker push registry.heroku.com/ospc-$(MODE)/web
	heroku container:release web -a ospc-$(MODE)
