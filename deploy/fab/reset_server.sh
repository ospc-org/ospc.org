#!/bin/bash
export rs="reset_server.sh STATUS: "
echo $rs activate aei_dropq
export DEP=/home/ubuntu/deploy
source /home/ubuntu/miniconda2/bin/activate aei_dropq
pushd ${DEP}
python setup.py install
popd
conda config --set always_yes true
conda clean --all
conda install pandas=0.20.1
echo $rs get taxpuf package
cd $DEP
export TAXPUF_CHANNEL="https://conda.anaconda.org/t/$(cat /home/ubuntu/.ospc_anaconda_token)/opensourcepolicycenter"
conda config --add channels $TAXPUF_CHANNEL
conda install taxpuf
rm -rf puf.csv.gz rm puf.csv
write-latest-taxpuf && gunzip -k puf.csv.gz
export SUPERVISORD_CONF=/home/ubuntu/deploy/fab/supervisord.conf
echo $rs stop all
supervisorctl -c $SUPERVISORD_CONF stop all
# supervisord -c $SUPERVISORD_CONF
# supervisorctl -c $SUPERVISORD_CONF stop all

for repeat in 1 2 3;
    do
        bash ${DEP}/taxbrain_server/scripts/ensure_procs_killed.sh flask;
        bash ${DEP}/taxbrain_server/scripts/ensure_procs_killed.sh celery;
        sleep 2;
    done
cd $DEP/..
echo $rs configure conda
conda config --set always_yes yes --set changeps1 no
echo $rs remove old versions
conda remove taxcalc; pip uninstall -y taxcalc
conda remove ogusa ; pip uninstall -y ogusa
conda remove btax ; pip uninstall -y btax
echo $rs Install taxcalc
cd $DEP/.. && rm -rf Tax-Calculator B-Tax OG-USA
git clone http://github.com/open-source-economics/Tax-Calculator
cd Tax-Calculator && git fetch --all && git fetch origin --tags && git checkout $TAXCALC_VERSION
if [ "$TAXCALC_INSTALL_LABEL" = "" ];then
    export TAXCALC_INSTALL_LABEL=" -c ospc ";
fi
if [ "$BTAX_INSTALL_LABEL" = "" ];then
    export BTAX_INSTALL_LABEL=" -c ospc ";
fi
if [ "$OGUSA_INSTALL_LABEL" = "" ];then
    export OGUSA_INSTALL_LABEL=" -c ospc ";
fi
if [ "$TAXCALC_INSTALL_METHOD" = "git" ];then
    python setup.py install
else
    conda install $TAXCALC_INSTALL_LABEL taxcalc=$TAXCALC_VERSION
    conda list | grep 'taxcalc' | awk -F' ' '{print $2}' | xargs -n 1 git checkout
fi
echo $rs Install OG-USA
if [ "$OGUSA_INSTALL_METHOD" = "git" ];then
    cd $DEP/..
    git clone http://github.com/open-source-economics/OG-USA
    cd OG-USA && git fetch --all && git fetch origin --tags && git checkout $OGUSA_VERSION && python setup.py install
else
    conda install $OGUSA_INSTALL_LABEL ogusa=$OGUSA_VERSION
fi
echo $rs Install B-Tax
if [ "$BTAX_INSTALL_METHOD" = "git" ];then
    cd $DEP/..
    git clone http://github.com/open-source-economics/B-Tax
    export BTAX_CUR_DIR=`pwd`/B-Tax/btax
    cd B-Tax && git fetch --all && git fetch origin --tags && git checkout $BTAX_VERSION && python setup.py install
else
    conda install $BTAX_INSTALL_LABEL btax=$BTAX_VERSION
fi

# TODO LATER
# conda install -c ospc btax --no-deps
echo $rs redis-cli FLUSHALL
redis-cli FLUSHALL

cd ${DEP}/../Tax-Calculator && git fetch origin
conda list | grep 'taxcalc' | awk -F' ' '{print $2}' | xargs -n 1 git checkout
cp ~/deploy/puf.csv.gz ./ && gunzip -k puf.csv.gz
cd taxcalc/tests
echo $rs Test the correct puf is here - Tax-Calculator
py.test -m "requires_pufcsv"
cd $DEP/taxbrain_server/tests
echo $rs Test the mock celery - mock flask tests in deploy
MOCK_CELERY=1 TAX_ESTIMATE_PATH=$OGUSA_PATH py.test -p no:django -v
cd $DEP
conda list
echo $rs Remove asset_data.pkl and recreate it with btax execute
rm -f asset_data.pkl
python -c "from btax.execute import runner;runner(False,2013,{})"
echo $rs supervisorctl -c $SUPERVISORD_CONF start all
conda clean --all
supervisorctl -c $SUPERVISORD_CONF start all
python -c "from taxcalc import *;from btax import *;from ogusa import *" && ps ax | grep flask | grep python && ps ax | grep celery | grep python && echo $rs RUNNING FLASK AND CELERY PIDS ABOVE
echo $rs DONE - OK
