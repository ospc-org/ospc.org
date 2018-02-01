#!/bin/bash

set -e

# Paths to the requirements files that are installed.
REQS_FILES=(
  ../requirements.txt
  ../requirements_dev.txt
  requirements.txt
)

# Path to the log directory.
LOGDIR=taxbrain_server/logs

echo '*** Creating environment ***'
export HAS_ENV=1
conda env remove --name aei_dropq
conda env create --file fab/dropq_environment.yml

echo '*** Installing conda requirements ***'
CHANNEL='-c ospc/label/dev -c ospc '
for pkg in $(cat ../conda-requirements.txt); do
  if [[ ! $pkg =~ btax|ogusa|taxcalc ]]; then
    echo "Installing ${pkg}..."
    conda install $channel $pkg -y
  fi
done

echo '*** Installing package requirements ***'
install_conda_reqs
for reqs in "${REQS_FILES[@]}"; do
  echo "pip install -r $reqs"
  pip install -r $reqs
done
pip uninstall -y taxbrain_server
pip install -e .

echo "*** Re-initializing logs directory: ${LOGDIR} ***"
rm -rf taxbrain_server/logs
mkdir taxbrain_server/logs

echo "DONE"

