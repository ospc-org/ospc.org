import os

def set_env():
    HOME = os.environ.get('WORK_DIR') or '/home/ubuntu'
    BTAX_CUR_DIR = os.path.join(HOME, 'B-Tax')
    TAX_ESTIMATE_PATH = OGUSA_PATH = os.path.join(HOME, 'OG-USA', 'Python')
    MOCK_CELERY = bool(int(os.environ.get('MOCK_CELERY', 0)))
    ENV_DEFAULTS = dict(WORK_DIR=HOME,
                        BTAX_CUR_DIR=BTAX_CUR_DIR,
                        TAX_ESTIMATE_PATH=TAX_ESTIMATE_PATH,
                        OGUSA_PATH=OGUSA_PATH,
                        REDISGREEN_URL="redis://localhost:6379",
                        CELERYD_PREFETCH_MULTIPLIER="1",
                        MOCK_CELERY=MOCK_CELERY)
    ENV = {}
    for k, v in ENV_DEFAULTS.items():
        ENV[k] = os.environ.get(k, v)
        os.environ[k] = str(ENV[k]) if not isinstance(v, bool) else str(int(v))
    globals().update(ENV)
    return ENV
