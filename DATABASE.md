** Database Setup **

Due to our reliance on the Postgres JSON field, a local Postgres installation
is required to run the app and its tests locally. We recommend that you follow
the [Heroku instructions](https://devcenter.heroku.com/articles/heroku-postgresql#local-setup) for local Postgres installation. Postgres 9.4 is run in production, and this is the version that
is recommended for local development. To install this version, go to the
potgres.app page [for installing legacy versions](https://postgresapp.com/documentation/all-versions.html)
and download the installer for Postgres 9.4.

PolicyBrain has not been tested on newer versions of Postgres. Thus, we cannot
help you if you run into problems on a new version of Postgres. Older versions
of Postgres (< 9.4) do not have as much support for operations on the JSON
field. Thus, we cannot guarantee that the PolicyBrain will work with older
versions.

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
