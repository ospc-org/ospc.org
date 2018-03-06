# deploy

How to run webapp-public locally.
* Clone this `deploy` repo, then `cd` into the `fab` directory and run: `conda env create --file dropq_environment.yml --name aei_dropq && source activate aei_dropq`
* Follow the instructions for [the `taxpuf` package installation](https://github.com/OpenSourcePolicyCenter/taxpuf) and run `write-latest-taxpuf` from the `deploy` repo clone top dir.
* Then install Tax-Calculator, OG-USA, B-Tax, and webapp-public into the `aei_drop` environment using conda packages or installations from source.  An example is:
```
conda install -c ospc taxcalc ogusa btax # install the latest from "main" ospc channel
```
* Copy `run_flask_server.sh` to `run_flask_server_local.sh` so you can edit it.  *Do not commit changes* to `run_flask_server.sh` unless the changes are specific to the deployed EC2 box settings.
* Copy `run_celery.sh` to `run_celery_local.sh` so you can edit it.  Same comment about changes to `run_celery.sh`.
* Edit `run_flask_server_local.sh` and `run_celery_local.sh` to define the environment variables in there.  Here's an example of `run_flask_server_local.sh` for me:
```
#!/usr/bin/env bash
export C=/Users/peter/Documents
BTAX_CUR_DIR='$C/AEI/B-Tax/btax/' TAX_ESTIMATE_PATH="$C/AEI/OG-USA/Python" OGUSA_PATH="$C/AEI/OG-USA/Python/" REDISGREEN_URL="redis://localhost:6379" python flask_server.py
```
In the example above, I use the environment variable `C` for where I clone repos, then I create the `BTAX_CUR_DIR` variable as the `btax` directory in the B-Tax clone, `TAX_ESTIMATE_PATH` for OG-USA's `Python` dir and `OGUSA_PATH` to that `Python` dir as well.  `REDISGREEN_URL` tells the server where to look for `redis` to be running.  The env variables are prepended to `python flask_server.py` so the variables apply in that process but are not set in the calling environment.

Then in one terminal, run:
```
. run_flask_server_local.sh
```
Next edit `run_celery_local.sh` to something like this:
```
#!/usr/bin/env bash
export C=/Users/peter/Documents
BTAX_CUR_DIR='$C/AEI/btax_new/btax/' TAX_ESTIMATE_PATH="$C/AEI/OG-USA/Python" OGUSA_PATH="$C/AEI/OG-USA/Python/" REDISGREEN_URL="redis://localhost:6379" CELERYD_PREFETCH_MULTIPLIER=1 celery -A celery_tasks worker --concurrency=1 -P eventlet -l info
```
Basically just change the env variables that are related to where you cloned things as done for

`. run_flask_server_local.sh`

In a separate terminal tab or window, run:

```
. run_celery_local.sh
```

Next, start redis:
```
redis-server
```

Finally, [start your webapp-public django app](https://github.com/OpenSourcePolicyCenter/webapp-public/), following the instructions there for `migrate.py` and `runserver.py`.  Note that when running webapp-public's Django app locally, you can use environment variables to set where each type of compute job is being sent:

 * `TAXCALC_WORKERS`: Where to send /taxbrain jobs
 * `BTAX_WORKERS`: Where to send /ccc jobs
 * `OGUSA_WORKERS`: Where to send dynamic models

An example of running webapp-public locally while using an EC2 box as a Tax-Calculator, OG-USA, and B-Tax worker:

```
TAXCALC_WORKERS=54.164.155.6 BTAX_WORKERS=54.164.155.6 OGUSA_WORKERS=54.164.155.6 python manage.py runserver
```
More than one IP address can be given for each of the `*_WORKER` env variables if separated by commas.

If you want to test your local webapp-public django app versus an EC2 box, then prepend `DROPQ_WORKERS`, `BTAX_WORKERS`, or `OGUSA_WORKERS` to your running of celery and flask.  For example to send all jobs to IP addresses `1.2.3.4` and `2.3.4.5`, do the following 2 commands in separate terminal tabs or windows:
```
DROPQ_WORKERS=1.2.3.4,2.3.4.5 BTAX_WORKERS=1.2.3.4,2.3.4.5 OGUSA_WORKERS=1.2.3.4,2.3.4.5 . run_celery_local.sh
DROPQ_WORKERS=1.2.3.4,2.3.4.5 BTAX_WORKERS=1.2.3.4,2.3.4.5 OGUSA_WORKERS=1.2.3.4,2.3.4.5 . run_flask_server_local.sh
```
