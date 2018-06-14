About PolicyBrain
---------------------------

PolicyBrain provides a platform for open-source policy simulation models.  It serves as an interface to powerful models for those who do not want to work directly with the models themselves.  PolicyBrain’s primary jobs are to send the user-input to the models, provide feedback if the user-input causes warnings or errors, schedule jobs on available machines, retrieve the results from the models, and deliver the results to the user.  Essentially, PolicyBrain provides the infrastructure and resources for the models that it hosts.

The apps that are currently hosted are TaxBrain and Cost-of-Capital Calculator.  TaxBrain enables the user to perform static and dynamic analyses on their specified personal income tax reform.  Cost-of-Capital Calculator enables the user to perform a static analysis on their specified business tax reform.

PolicyBrain is a Django app which is deployed on Heroku and uses Flask, Celery, and Redis to schedule jobs.  

- Website: https://www.ospc.org/
- Mailing List: https://www.freelists.org/list/policybrains_modelers

Release Process
---------------

To review the steps for the release process, see [RELEASE_PROCESS.md](https://github.com/OpenSourcePolicyCenter/webapp-public/blob/master/RELEASE_PROCESS.md)


Local Deployment Setup
---------------------------------

First, if you plan on contributing to PolicyBrain, then fork PolicyBrain and work off of that fork.  If you do not plan to contribute, then you can clone the main repo.

Make sure that [Anaconda/Miniconda](https://www.anaconda.com) are installed. Make sure that the local Postgres Server is running. Then, open a terminal
window and run the following commands using bash:
```
# swap out YOURUSERNAME with OpenSourcePolicyCenter if you did not fork this project and
# your user name if you did
git clone https://github.com/YOURUSERNAME/PolicyBrain.git
cd PolicyBrain
git remote add upstream https://github.com/OpenSourcePolicyCenter/PolicyBrain
conda install -c ospc taxcalc btax
./python_env_build.sh
export DATABASE_USER=YOUR_POSTGRES_USERNAME DATABASE_PW=YOUR_POSTGRES_PASSWORD
source activate pb_env && source webapp_env.sh
python manage.py collectstatic
python manage.py migrate
python manage.py runserver
```
Now, the Django app should be up and running.  You can access the local instance of https://www.ospc.org/ at http://localhost:8000.  Next, set up Redis, Flask, and Celery.  This step allows you to submit and run jobs.
These services are configured via Docker in a docker-compose file. You need access to these images for the following commands to work. See DOCKER.md for more information.
```
# Login to docker with `docker login`
# Go to the PolicyBrain/distributed directory
cd PolicyBrain/distributed
docker-compose up -d
```

Now, that the server has been installed, you can start it up simply by running:

```
export DATABASE_USER=YOUR_POSTGRES_USERNAME DATABASE_PW=YOUR_POSTGRES_PASSWORD
source activate pb_env && source webapp_env.sh
python manage.py runserver
```

and in another terminal window, run:

```
docker-compose up -d
```
