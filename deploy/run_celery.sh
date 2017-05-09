#!/usr/bin/env bash
BTAX_CUR_DIR='/home/ubuntu/B-Tax/' TAX_ESTIMATE_PATH="/home/ubuntu/OG-USA/Python" OGUSA_PATH="/home/ubuntu/OG-USA/Python/" REDISGREEN_URL="redis://localhost:6379" CELERYD_PREFETCH_MULTIPLIER=1 /home/ubuntu/miniconda2/envs/aei_dropq/bin/celery -A celery_tasks worker --concurrency=1 -P eventlet -l info

