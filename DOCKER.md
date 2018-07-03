Instructions for Setting Up Docker
-----------------------------------

1. Install the stable community edition of Docker. Install the version that
corresponds to your operating system from this [page](https://docs.docker.com/install/).
Make sure the docker app is running. You should see a whale icon in your
toolbar. If you are not on a Mac, see the [docker-compose installation page](https://docs.docker.com/compose/install/)
for information on how to set this up on your operating system.
2. Get the docker image:
  - Pull them from docker hub
    1. The docker image contains sensitive data and thus, it cannot be
    pulled freely. Contact me (henry.doupe@aei.org) if you think that
    you need this image. If approved, I will grant your docker hub account
    access to this repository.
    2. Next, login to docker at the command line with the command
    `docker login`, and enter your information.
    3. You can start the service by running:
    `cd PolicyBrain/distributed && docker-compose up -d`
    This will pull the required images, configure them, and run them in a
    detached state. Remove the `-d` flag to run them in the foreground.
  - Build them locally
    This may be useful if you do not have access to the sensitive data. With
    this process, you can run PolicyBrain using only non-sensitive data.
    1. go to the `distributed` directory.
    2. run
    ```
    export PB_VERSION='type current PolicyBrain version here'
    docker build -t opensourcepolicycenter/distributed:$PB_VERSION ./
    docker build -t opensourcepolicycenter/celery:$PB_VERSION --build-arg TAG=$PB_VERSION --file Dockerfile.celery ./
    docker build -t opensourcepolicycenter/flask:$PB_VERSION --build-arg TAG=$PB_VERSION --file Dockerfile.flask ./
    ```
3. Depending on your system you may have to tweak the Docker memory and CPU
usage limits. I find that I can do most runs with RAM set around 8 GB and
CPU at 1 or 2. Your mileage may vary. Some of the more memory intensive runs
such as Tax-Calculator simulations with the CPS file require RAM up to 12 or 13
GB when using docker. You may have problems doing those runs locally.
Adjust these parameters by clicking the docker icon in the toolbar,
selecting preferences, and click the "Advanced" icon. Make sure to click
"Apply & Restart" so that the adjustments will go into effect.

Build and Deploy Docker Images
--------------------------------
- Build worker node images: `make dist-build -e TAG=$TAG`
- Build webapp image: `make webapp-build -e TAG=$TAG`
- Push worker node images: `make dist-push -e TAG=$TAG`
- Push webapp image: `make webapp-push -e TAG=$TAG -e VERSION=$VERSION`
- Release webapp image: `make webapp-release -e VERSION=$VERSION`

Note:
- `TAG` refers to the GitHub release version or local branch
- `VERSION` refers to the app type, either test (`test`) or production (`prod`)
- The OSPC token is not required if the PUF is not required

Other useful commands
-------------------------
- View logs
Get Container ID:
`docker ps`
Follow log of service with that ID:
`docker logs -f CONTAINER_ID`

- View CPU and memory usage:
`docker stats`

- Experiment within the `distributed` container
`docker run -it opensourcepolicycenter/distributed`

- More to come...
