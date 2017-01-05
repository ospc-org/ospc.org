Taxbrain Web Application
========================

# Deploying To Heroku

Production
----------
Heroku relies upon GIT for deployment.  The following commands are for deployment.  Before deploying to Heroku make certain to run the following command* locally and commit the changes:

`./manage.py collectstatic --noinput`

###### * Currently this command fails to create the staticfiles dir on Heroku, so this has to be run locally and the changes committed.

Deploy to Heroku:

`git push heroku master`

If any of the models have been updated in a deployment then those changes have to migrated so the database schema is updated.  The migration should be created locally, committed, and pushed to Heroku as opposed to running the makemigration command on Heroku.  Locally run the following:

`./manage.py makemigrations` or `python manage.py makemigrations` (both commands have the same effect.)

Commit the files that are created.

In order to run those migrations, run the following commands:

`heroku run ./manage.py migrate` or `heroku run python manage.py migrate` (both commands have the same effect.)

Your schema will now be udpated.

*DEBUG*:  This should always be False on the production site.  Make certain the environment variable DEV_DEBUG is set to anything but the string 'True'.  To check what variables are set to in Heroku's environment run the following command:

`heroku config`

This will list all config variables (alternatively go to the Settings section on the Heroku dashboard and click the 'Reveal Config Vars' button.)

Development
-----------
A live development server works exactly the same way as a production server on Heroku does.  All commands and configurations are the same.  The only difference is that the requirements_dev.txt can be used on this server to have access to the various debugging tools.

Post deployment to a dev server runt he following command in order to install the dev tools (if desired):
`heroku run pip install -r requirement_dev.txt`

The migration commands presented in the Production section also hold true for development.  Post deployment make sure to run the migration commands.

*DEBUG*: In order to turn DEBUG on, set the DEV_DEBUG environment variable to the string 'True'.  DEBUG will be off id set to anything but 'True'.  In order to change the DEV_DEBUG variable use the following command:
`heroku config:set DEV_DEBUG='True'`

The above command will turn DEBUG on.  Setting to any other string will turn DEBUG off.


# Installing Locally
To develop the application locally, you need a script containing the environment variables necessary for communicating with the computation nodes. You should ask your project manager or administrator for this script.

## Installing PostgreSQL
Postgres is used for this project.  If PostgreSQL is not installed on your machine follow the instructions in the following links.

OS X:
http://www.postgresql.org/download/macosx/

Ubunutu:
https://help.ubuntu.com/community/PostgreSQL

Windows (should support 7 & 8):
http://www.postgresql.org/download/windows/

## Create database taxcalc
After PostgreSQL has been successfully installed make sure to create the taxcalc database.

For Ubuntu the command is:
```
createdb taxcalc
```

If you need to add a user and grant permissions make sure to have psql installed as well.

## Create a directory
Make sure to create a directory wherever you keep your projects.

```
mkdir project_name
```

## Clone the repo in the new directory

```
git clone git@github.com:OpenSourcePolicyCenter/webapp.git
```

## Create a conda environment for your local development

```
conda create -n webapp pip python=2.7
source activate webapp
```

Install the required packages listed in the conda-requirements.txt file. taxcalc
package is kept in a conda channel:

```
conda install --file conda-requirements.txt -c ospc
```

Then use pip to install the remaining packages

```
pip install -r requirements.txt
```

then:

```
pip install -r requirements_dev.txt
```

## Using foreman
Since Django can be a more involved process using foreman might be a better tool for some situations.  If no work will be done on the back end, then foreman might be the tool of choice (although once Django is setup all you will have to do is run the server locally to make use of it.)

Some important points:
- You must start the virtual environment.
- The Heroku toolbar that is installed with the requirements.txt file is expecting PostgreSQL to exist on your system.

After the environment is activated the following command will start foreman:
```
foreman start
```
Once the server has started foreman will use port 5000.

## Building Static Files
To setup your environment for building static assets:
```bash 
npm install
npm install -g bower
bower install
```

To compile LESS assets:
```bash 
gulp less
```

Collect static files and make sure changes get committed back:
```bash 
python manage.py collectstatic
```

## Using Django
Once all the dependecies are installed a couple of commands are necessary to get the Django project up and running and onto ```./manage.py runserver```.  Make sure the virtual environment is activated.

### First update the settings.py file located in the webapp dir (webapp/settings.py)
In the settings.py file there is a database configuration that looks like:

```
DATABASES = {
'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'taxcalc',
    'USER': 'postgres',
    'PASSWORD': '',
    'HOST': '',
    'PORT': '5432',
    }
}
```
1) Change the USER to your user name (the one you used to setup Postgres).
2) Change the PASSWORD to the password you used to setup Postgres.
3) Change HOST to 127.0.0.1

# PLEASE DO NOT COMMIT YOUR LOCAL CHANGES TO THE DATABASE CONFIG IN THE SETTINGS FILE.  GIT STASH THEM! 
## ALTERNATIVELY, STOP TRACKING LOCAL CHANGES TO THIS FILE WITH:
## `git update-index --assume-unchanged webapp/settings.py`

Next change the DEBUG & TEMPLATE_DEBUG settings to True.

### Second migrations have to been run.  Migrations manage the schema for all database objects.  Go to the root of the project simply run:
```
./manage.py migrate
```
Django will then run the migrations and all the tables will be created in the db.  NOTE: it is critical that migrations are run when updating models, otherwise the changes to the models will not be recognized and errors will be thrown by Django (these errors tend to be increasingly informative and you will usually be prompted by Django that there are unmigrated changes when you run the local server.)

### Third, it's time run the server.  Simply run:
```
./manage.py runserver
```

Now you have a live project being run locally!
