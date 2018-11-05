OSPC_ANACONDA_TOKEN := `cat ~/.ospc_anaconda_token`
NEW_RELIC_TOKEN := `cat ~/.newrelic-$(MODE)`

dist-build:
	cd distributed && \
	docker build -t distributed:$(TAG) ./ --build-arg PUF_TOKEN=$(OSPC_ANACONDA_TOKEN) && \
	docker build --no-cache --build-arg TAG=$(TAG) -t flask:$(TAG) --file Dockerfile.flask ./ && \
	docker build --no-cache --build-arg TAG=$(TAG) -t celery:$(TAG) --file Dockerfile.celery ./

dist-push:
	cd distributed && \
	docker tag distributed:$(TAG) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/distributed:$(TAG) && \
	docker tag flask:$(TAG) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/flask:$(TAG) && \
	docker tag celery:$(TAG) $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/celery:$(TAG) && \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/distributed:$(TAG) && \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/flask:$(TAG) && \
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/celery:$(TAG)

dist-test:
	cd distributed && \
	docker-compose rm -f && \
	docker-compose run flask py.test -s -v && \
	docker-compose rm -f

webapp-build:
	docker build --build-arg NEW_RELIC_TOKEN=$(NEW_RELIC_TOKEN) -t web:$(TAG) ./

webapp-push:
	docker tag ospc-web:$(TAG) registry.heroku.com/ospc-$(MODE)/web
	docker push registry.heroku.com/ospc-$(MODE)/web

webapp-release:
	heroku container:release web -a ospc-$(MODE)
