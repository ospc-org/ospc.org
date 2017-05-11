#!/bin/bash
install_env(){
    export has_env=1;
    conda env list | grep aei_dropq &> /dev/null || export has_env=0;
    if [ "$has_env" = "1" ];then
        conda env update --file fab/dropq_environment.yml || return 1;
    else
        conda env create --file fab/dropq_environment.yml || return 1;
    fi
    return 0;
}

install_reqs(){
    source deactivate
    install_env || return 1;
    source activate aei_dropq || return 1;
    pip install -r requirements.txt || return 1;
    for repo in btax ogusa taxcalc;do
        pip uninstall -y $repo &> /dev/null;
        conda remove $repo &> /dev/null;
    done
    conda install -c ospc taxcalc ogusa btax || return 1;
    pip uninstall -y taxbrain_server || return 1;
    python setup.py develop || return 1;
    return 0;
}
install_reqs