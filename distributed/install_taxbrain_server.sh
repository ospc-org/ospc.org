#!/bin/bash
install_env(){
    export has_env=1;
    conda env remove --name aei_dropq &> /dev/null;
    conda env create --file fab/dropq_environment.yml || return 0;
    return 0;
}
install_conda_reqs(){
    echo ---------------------------------------Installing conda requirements;
    channel="-c ospc/label/dev -c ospc "
    for pkg in $(cat ../conda-requirements.txt);do
        echo $pkg | grep -Eoi "(btax)|(ogusa)|(taxcalc)" &> /dev/null || echo install $channel $pkg && conda install $channel $pkg -y || return 1;
    done
}
install_reqs(){
    install_conda_reqs || return 1;
    echo Install webapp-public requirements.txt
    pip install -r ../requirements.txt || return 1;
    echo Install webapp-public requirements_dev.txt
    pip install -r ../requirements_dev.txt || return 1;
    echo Install requirements.txt of the deploy folder;
    pip install -r requirements.txt || return 1;
    pip uninstall -y taxbrain_server &> /dev/null;
    pip install -e . || return 1;
    rm -rf taxbrain_server/logs
    mkdir taxbrain_server/logs || return 1;
    return 0;
}
msg(){
    echo Local server installation complete!
    return 0;
}
install_env && source activate aei_dropq && install_reqs && msg || echo FAILED
