import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as f:
    longdesc = f.read()

config = {
    'description': 'TaxBrain Server - Flask and Celery Workers for OSPC Models',
    'url': 'https://github.com/OpenSourcePolicyCenter/webapp-public',
    'download_url': 'https://github.com/OpenSourcePolicyCenter/webapp-public',
    'description': 'taxbrain_server',
    'long_description': longdesc,
    'license': 'MIT',
    'packages': ['taxbrain_server',
                 'taxbrain_server.scripts'],
    'include_package_data': True,
    'name': 'taxbrain_server',
    'entry_points': {
         'console_scripts': [
             'taxbrain-flask-worker = taxbrain_server.flask_server:main',
             'taxbrain-celery-worker = taxbrain_server.celery_tasks:main',
             'taxbrain-run-all = taxbrain_server.local_proc_mgr:main',
        ]
    },
    'install_requires': [],
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    'tests_require': ['pytest']
}

setup(**config)
