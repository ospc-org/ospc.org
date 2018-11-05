# Distributed deploy instructions

1. Build and push images to AWS container registry
    ```
    export TAG= AWS_ACCOUNT_ID= AWS_REGION=
    rm -rf PolicyBrain
    git clone https://github.com/OpenSourcePolicyCenter/PolicyBrain
    cd PolicyBrain
    git fetch origin
    git checkout -b $TAG $TAG

    make dist-build && make dist-push
    ```


2. Pull distributed images to AWS server
    ```
    sudo docker-compose down
    sudo docker-compose rm
    docker system prune --all
    sudo apt-get install awscli
    sudo apt-get install python3-pip
    pip3 install --upgrade awscli
    aws configure
    sudo $AWS_ACCOUNT_ID= $AWS_REGION=
    sudo $(aws ecr get-login --region $AWS_REGION --no-include-email)
    sudo REPO=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com TAG=$TAG
    sudo docker-compose up -d
    ```
