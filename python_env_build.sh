echo 'appending channels'
conda config --append channels ospc/label/dev
conda config --append channels ospc
conda config --append channels conda-forge

echo 'creating environment pb_env and installing conda packages'
conda create -n pb_env python=2.7.14 taxcalc=0.17.0 btax=0.2.2 ogusa=0.5.8 numba>=0.33.0 pandas>=0.22.0 bokeh=0.12.7 nomkl gevent pillow pyparsing
echo 'successfull created env: pb_env'

echo 'activating env: pb_env'
source activate pb_env

echo 'pip installing remaining requirements'
pip install -r requirements.txt
pip install -r requirements_dev.txt
