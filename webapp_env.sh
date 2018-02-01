source activate aei_dropq

export NUM_BUDGET_YEARS=10
export DEV_DEBUG=True
export HTML_MINIFY=True

export OGUSA_WORKERS=127.0.0.1:5050
export DROPQ_WORKERS=127.0.0.1:5050
export BTAX_WORKERS=127.0.0.1:5050

export REDISGREEN_URL=redis://localhost:6379
export CELERYD_PREFETCH_MULTIPLIER=1
export ENFORCE_VERSION=False
export ENABLE_QUICK_CALC='True'
