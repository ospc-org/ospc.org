#!/bin/bash
source deactivate
install_env(){
    export has_env=1;
    conda env remove --name aei_dropq &> /dev/null;
    conda env create --file fab/dropq_environment.yml || return 1;
    return 0;
}
install_conda_reqs(){
    for pkg in $(cat ../conda-requirements.txt);do
        echo $pkg | grep -Eoi "(btax)|(ogusa)|(taxcalc)" &> /dev/null || echo install $pkg && conda install $pkg || return 1;
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
    python setup.py develop || return 1;
    return 0;
}
msg(){
    echo Last step: Install taxcalc ogusa and btax via conda or setup.py install;
    echo See the Tax-Calculator README and README_local_development.md on installing those;
    return 0;
}
install_env && source activate aei_dropq && install_reqs && msg || echo FAILED
