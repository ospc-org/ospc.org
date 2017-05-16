#!/bin/bash
export WEBAPP_DIR=`pwd`
if [ "$OSPC_INSTALL_CHANNEL" = "" ];then
    export OSPC_INSTALL_CHANNEL=ospc;
fi
source deactivate
install_webapp_public(){
    conda config --set always_yes yes --set changeps1 no;
    conda update -n root conda;
    cd $WEBAPP_DIR/deploy && . install_taxbrain_server.sh || return 1;
    cd $WEBAPP_DIR || return 1;
    source activate aei_dropq || return 1;
    conda install -c $OSPC_INSTALL_CHANNEL --file conda-requirements.txt || return 1;
    pip install -r requirements.txt || return 1;
    pip install -r requirements_dev.txt || return 1;
    pip install pytest-django || return 1;
    pip install pytest-xdist || return 1;
    export AWS_STORAGE_BUCKET_NAME=taxbraingzipped
    export SECRET_KEY="abcde%!z@cu@o29$zjifeoudt1ute&0ii33!8huud71&4#l2#817pei";
    return 0;
}
install_webapp_public