conda config --add channels ospc
conda config --add channels ospc/label/dev
conda config --append channels conda-forge

conda create -n pb_env python=2.7.14 \
    taxcalc=0.15.2 \
    btax=0.2.2 \
    ogusa=0.5.8 \
    numba>=0.33.0 \
    pandas>=0.22.0 \
    bokeh=0.12.7 \
    nomkl \
    gevent \
    pillow \
    pyparsing \

source activate pb_env

pip install -r requirements.txt
pip install -r requirements_dev.txt
