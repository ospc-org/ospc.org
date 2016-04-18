# OSPC Webapp
<!---
  @todo Add code status indicators?
    Possible services include codeclimate, travis, codeship, coveralls, inch-ci, hakiri
    Examples:
  [![Build Status](https://codeship.com/projects/0e40c6d0-4787-0132-ccf4-025f0fbdfe45/status?branch=master)](https://codeship.com/projects/0e40c6d0-4787-0132-ccf4-025f0fbdfe45)
  [![Build Status](https://secure.travis-ci.org/angular-ui/bootstrap.svg)](http://travis-ci.org/angular-ui/bootstrap)
  [![Code Climate](https://codeclimate.com/github/wellbredgrapefruit/asari.png)](https://codeclimate.com/github/wellbredgrapefruit/asari)
  [![Security](https://hakiri.io/github/wellbredgrapefruit/asari/master.svg)](https://hakiri.io/github/wellbredgrapefruit/asari/master)
  [![Test Coverage](https://img.shields.io/coveralls/resque/resque/master.svg)](https://coveralls.io/r/resque/resque)
  [![Inline Doc Coverage](http://inch-ci.org/github/resque/resque.svg)](http://inch-ci.org/github/resque/resque)
-->
Webapp is a Python/Django-based web serving application for the Open Source
  Policy Center. It serves static pages with information on the OSPC and
  provides GUI access to its apps.

* [Getting Started](#getting-started)
  * [Requirements](#requirements)
  * [Installation](#installation)
  * [Database Setup](#database-setup)
  * [Debug Flags](#set-debug-flags)
  * [Bower](#bower)
* [Running the App](#running-the-app)
  * [Using Django](#using-django)
  * [Using Foreman](#using-foreman)
* [Making Changes](#making-changes)
* [Deploying to Heroku](#deploying-to-heroku)

<!---
  @todo Add these items?
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
-->

## Getting started

### Requirements

To install and use Webapp you will need:

* [Python](https://www.python.org/downloads/) - 2.7 or 3.4 is fine as it's just
  used to build the Conda virtual environment where WebApp sets up its own 2.7
  copy. However, you MUST use the x64 version, or else pandas will run out of
  memory when importing tax data.
* [Anaconda](http://continuum.io/downloads) or
  [Miniconda](http://conda.pydata.org/miniconda.html)

Additionally, if you will be making CSS or JS changes you will need:

* [Bower](http://bower.io/) (which requires Node.js and NPM) for vendor files
* A LESS compiler. Node's can be installed with `npm install less -g` and used
  with `lessc path/to/source.lss > path/to/dest.css`

By default the application will use a SQLite database, which requires no
  additional steps. However, if you'd like to use PostgreSQL you will need:

* PostgreSQL database server: [OS X](http://www.postgresql.org/download/macosx/),
   [Ubunutu](https://help.ubuntu.com/community/PostgreSQL),
   [Windows](http://www.postgresql.org/download/windows/).
* If you're on Windows, the Postgres adapter requires a couple more steps:
  * It used to be possible to succeed in installing the psycopg2 library with
  the below:
    * add Postgres's bin folder to your path (i.e. C:\Devtools\PostgreSQL\9.4\bin)
    * install the
    [Microsoft Visual C++ Compiler for Python](http://www.microsoft.com/en-us/download/details.aspx?id=44266)
    to compile some supporting libraries distributed as source
  * Now, until [this issue](https://github.com/nwcell/psycopg2-windows/issues/4)
  is fixed, you must instead follow these steps:
    * Install a copy of Python 2.7 to your PATH (needed for below installer)
    * Install Windows pre-compiled binaries from
    [here](http://www.stickpeople.com/projects/python/win-psycopg/)
    * Move the resulting folder into your conda env
    * Remove the explicit psycopg2 line from `requirements.txt`; it will never
    validate but you should be able to use the library.
    * Ensure to add local gitignore to `requirements.txt` since you've changed it.


### Installation

#### Clone the repo into a new directory
Navigate to your web projects directory and use git to clone the project files
into a new directory:

via SSH
```
git clone git@github.com:OpenSourcePolicyCenter/webapp.git
```

or via HTTPS
```
git clone https://github.com/OpenSourcePolicyCenter/webapp
```

#### Use Conda to install libraries

Conda manages a virtual environment of python libraries and sources. The files
  `.condarc` and `conda-requirements` are used by the Heroku Conda buildpack to
  accomplish this on Herkou servers. Locally, you should use the provided
  `environment.yml` instead:

* Create a conda environment and load this project's dependencies
  * `conda env create` (Note it will detect `environment.yml` automatically, but
  for future reference you can specify alternative environment files with
  `conda env create --file filename.yml`)
* Tell Conda to use it for our current session
  * `source activate ospc-webapp-public` (or simply `activate ospc-webapp-public` on Windows)
* If you ever need to deactivate it, you can use
  * `source deactivate` (`deactivate` on Windows)

##### Updating Conda Packages
Occasionally you will need to update conda's packages. Do this by activating your
environment, then `conda env update`.


#### Use Pip to install more libraries

Now that Conda has set up our virtual environment and downloaded Pip, we can use
  Pip to install the packages which Conda doesn't support directly into our
  environment.

```
pip install -r requirements_nopsycopg.txt
pip install -r requirements_dev.txt
```

If you'd like to use PostgreSQL, instead use:

```
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

#### Updating Pip libraries

```
pip install --upgrade -r requirements_nopsycopg.txt
pip install --upgrade -r requirements_dev.txt
```

Similarly for Postgres you would drop the "_nopsycopg" above.


### Database Setup

Webapp requires a database. By default this will be automatically set up and
configured by SQLite.

If you'd prefer to use Postgres:

* Set an environment variable `DATABASE_URL` in this format:
  * `os.environ['DATABASE_URL'] = 'postgres://user:password@localhost:port/dbname'`
* Then, create the taxcalc database on your PostgreSQL server and set up user
  permissions to match `settings.py`.
  * In Ubuntu you can create the database with `createdb taxcalc`. If you need to
  add a user and grant permissions make sure to have psql installed.
  * In Windows, use the pgAdmin tool.


#### Run migrations
Migrations manage the schema for all database objects. Ensure your Conda
environment is activated, then simply run

`python manage.py migrate`

from the repo root. Django will then run the migrations to create all the db tables.

*NOTE: After updating models, it is critical you rerun migrations. Otherwise, the
changes will not be recognized and errors will be thrown by Django
(these errors tend to be increasingly informative and you will usually be
prompted by Django that there are unmigrated changes when you run the local
server.)*


#### Create Superuser
You'll want an initial user with full privileges to navigate the backend.

`python manage.py createsuperuser`

This will prompt you interactively for a username and password.

#### Load initial data
Currently there is no seed data included in the application. If it's eventually
included, you can run

`python manage.py loaddata /full/path/to/data.json`

To include it into the database. This is meant to be loadable as a "fixture" as
well via Django, but we haven't been able to get that to work yet.

### Set debug flags
You'll likely want the DEV_DEBUG environment variable to the string 'True'
 before running the application.

### Bower

To make CSS or JS changes, you'll need to first download the latest version of
the vendor files with `bower install`.

Subsequent updates can be made with `bower update`.

## Running the App

### Using Django
Once all the dependencies are installed and settings configured you can start
the server with

`python manage.py runserver`

Now you have a live project running locally!

### Running dropQ
dropQ workers are required to run the tax calculator. Start them according to
dropQ's readme. To connect your workers to this webapp, set the environment
variable `DROPQ_WORKERS` to a comma-delineated list of worker addresses, e.g.
`DROPQ_WORKERS=localhost:5050`.

### Using foreman
Since Django can be a more involved process using foreman might be a better tool
for some situations.  If no work will be done on the back end,
then foreman might be the tool of choice (
although once Django is setup all you will have to do is run the server
locally to make use of it.)

Some important points:
- You must start the virtual environment.
- The Heroku toolbar that is installed with the requirements.txt file is
expecting PostgreSQL to exist on your system.

After the environment is activated the following command will start foreman:
```
foreman start
```
Once the server has started foreman will use port 5000.

## Making Changes

### CSS & JS

CSS changes must be made to the LESS source files in `static/less` and then
manually compiled to `static/css`, i.e. by running
`lessc static/less/taxbrain.lss > static/css/taxbrain.css`.

CSS and JS changes will not be reflected until their source versions from
`static` are moved to the deployed asset folder `staticfiles` with the command
`python manage.py collectstatic`.

There are asset pipelining solutions available for Django that would make the
above steps unneccesary, but we have not yet implemented them.

## Deploying To Heroku

### Local pre-deployment tasks

Before deploying to Heroku make certain to run the following command locally
and commit the changes:

`./manage.py collectstatic --noinput`

Currently this command fails to create the staticfiles dir on Heroku,
so this has to be run locally and the changes committed.

### Pushing with Git

Heroku relies upon GIT for deployment.

Deploy to Heroku:

`git push heroku master`