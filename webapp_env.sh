# if you want to use a user besides postgres,
# run `DATABASE_USER=yourusername source webapp_env.sh`
export DATABASE_NAME=policybrain_local_database
if [ -z ${DATABASE_USER+x} ]
then
    echo using database username postgres
    export DATABASE_USER=postgres
else
    echo using database username $DATABASE_USER
fi

export DATABASE_URL=postgresql://localhost/$DATABASE_NAME
if ! psql -l | grep $DATABASE_NAME
then
    echo creating database $DATABASE_NAME under username $DATABASE_USER
    createdb $DATABASE_NAME -U $DATABASE_USER
fi


export NUM_BUDGET_YEARS=10
export DEV_DEBUG=True
export HTML_MINIFY=True

export OGUSA_WORKERS=172.19.0.2:5050
export DROPQ_WORKERS=172.19.0.2:5050
export BTAX_WORKERS=172.19.0.2:5050

export REDISGREEN_URL=redis://172.20.0.2:6379
export CELERYD_PREFETCH_MULTIPLIER=1
export ENFORCE_VERSION=False
export ENABLE_QUICK_CALC='True'
