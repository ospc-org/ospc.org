** Database Setup **

Due to our reliance on the Postgres JSON field, a local Postgres installation
is required to run the app and its tests locally. We recommend that you follow
the [Heroku instructions](https://devcenter.heroku.com/articles/heroku-postgresql#local-setup) for local Postgres installation. Postgres 9.4 is run in production, and this is the version that
is recommended for local development. To install this version, go to the
potgres.app page [for installing legacy versions](https://postgresapp.com/documentation/all-versions.html)
and download the installer for Postgres 9.4. Other useful resources are a postgres
[installation video](https://www.youtube.com/watch?v=xaWlS9HtWYw) and the [Postgres.app installation documentation](http://postgresapp.com/documentation/install.html).

PolicyBrain has not been tested on newer versions of Postgres. Thus, we cannot
help you if you run into problems on a new version of Postgres. Older versions
of Postgres (< 9.4) do not have as much support for operations on the JSON
field. Thus, we cannot guarantee that the PolicyBrain will work with older
versions.

The default behavior is to work off of a local Postgres database
`policybrain_local_database`, and in `webapp_env.sh`, the Django database url
environment variable `DATABASE_URL` is set to `postgresql://localhost/policybrain_local_database`.
However, after running `source webapp_env.sh` you can update this variable
to point to other Postgres databases such as some other database named
`my_other_postgres_database`. Then, you update the database url to be
`postgresql://localhost/my_other_postgres_database`. This is useful if you
want to run some tests on the production or test app database, for example.


** Database Migrations **

- Be very careful with data related to the results column
- Do a monthly database back up and keep the previous two months of production
  backups and one month of testing backups
- Examine the python migration code created by Django
- Examine the SQL migration code created by Django
- Always back up your data before running a migration
- Check that you can roll back your migrations
- Check how long it will take to run a migration (most of ours are fairly
  quick)


** Database Backup Policy **

Heroku keeps a back up of our databases for up to five days. We should be able to roll back 
further if needed. Below is the procedure that we should use to maintain at least one
accurate, uncorrupted (if not up to date) database:
- Production database stays up and is the production database until it needs to be rolled back
- Back-up 1 is the previous version of the database where a version is defined by the
  database schema. If the schema is changed (i.e. migrations are run), the version is bumped up.
- Back-up 2 is the version preceding Back-up 1. 

The Production database and the Back-up 1 database are stored on Heroku. In order to keep costs down
Back-up 2 is stored at a separate location. I am actively exploring different options for storage. 

This procedure is not completely infallible. We could realize that the data is corrupted four versions
after a change was made. However, this procedure gives us a at least a month or two to realize that
something is wrong. Further, versions that precede large scale or complex migrations are saved for 
longer periods of time. For example, the databases from before [#738]([https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/738) and [#822](https://github.com/OpenSourcePolicyCenter/PolicyBrain/pull/822) were both stored.