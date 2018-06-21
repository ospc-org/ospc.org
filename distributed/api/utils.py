import os

def set_env():
    HOME = os.environ.get('WORK_DIR') or '/home/ubuntu'
    CELERY_BROKER_URL=os.environ.get('CELERY_BROKER_URL','redis://localhost:6379'),
    CELERY_RESULT_BACKEND=os.environ.get('CELERY_RESULT_BACKEND','redis://localhost:6379')
    BTAX_CUR_DIR = os.path.join(HOME, 'B-Tax')
    TAX_ESTIMATE_PATH = OGUSA_PATH = os.path.join(HOME, 'OG-USA', 'Python')
    MOCK_CELERY = bool(int(os.environ.get('MOCK_CELERY', 0)))
    ENV_DEFAULTS = dict(WORK_DIR=HOME,
                        BTAX_CUR_DIR=BTAX_CUR_DIR,
                        TAX_ESTIMATE_PATH=TAX_ESTIMATE_PATH,
                        OGUSA_PATH=OGUSA_PATH,
                        CELERY_BROKER_URL=CELERY_BROKER_URL,
                        CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND,
                        CELERYD_PREFETCH_MULTIPLIER="1",
                        MOCK_CELERY=MOCK_CELERY)
    ENV = {}
    for k, v in list(ENV_DEFAULTS.items()):
        ENV[k] = os.environ.get(k, v)
    globals().update(ENV)
    return ENV
