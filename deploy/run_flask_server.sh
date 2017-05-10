#!/usr/bin/env bash
if [ "$WORK_DIR" = "" ];then
    export WORK_DIR=/home/ubuntu
fi
BTAX_CUR_DIR="${WORK_DIR}/B-Tax/" TAX_ESTIMATE_PATH="${WORK_DIR}/OG-USA/Python" OGUSA_PATH="${WORK_DIR}/OG-USA/Python/" REDISGREEN_URL="redis://localhost:6379" taxbrain-flask-worker
