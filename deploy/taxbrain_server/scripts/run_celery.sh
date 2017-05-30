#!/usr/bin/env bash
source deactivate
export MINICONDA_DIR="$(dirname $(dirname $(which python)))"
if [ "$WORK_DIR" = "" ];then
    export WORK_DIR=/home/ubuntu;
fi
if [ "$OSPC_ENV_NAME" = "" ];then
    export OSPC_ENV_NAME=aei_dropq;
fi
run_celery(){
    ls $MINICONDA_DIR/bin/ &> /dev/null || return 1;
    ls $MINICONDA_DIR/envs/$OSPC_ENV_NAME &> /dev/null || return 1;
    source activate $OSPC_ENV_NAME;
    export BTAX_CUR_DIR="${WORK_DIR}/B-Tax/";
    export TAX_ESTIMATE_PATH="${WORK_DIR}/OG-USA/Python" ;
    export OGUSA_PATH="${WORK_DIR}/OG-USA/Python/";
    export REDISGREEN_URL="redis://localhost:6379";
    export CELERYD_PREFETCH_MULTIPLIER=1;
    ${MINICONDA_DIR}/envs/${OSPC_ENV_NAME}/bin/celery -A "taxbrain_server.celery_tasks" worker --concurrency=1 -P eventlet -l info || return 1;
}
run_celery
