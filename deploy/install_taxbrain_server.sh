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

# Name of the environment (in the dropq_environment.yml file).
AEI_ENV_NAME='aei_dropq'

# Defines a finction that prompts the user for a particular action.
prompt_user() {
  read -p "$1 [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

if prompt_user "Create / reset environment?"; then
  echo '*** Creating environment ***'
  if [[ $(conda env list) =~ $AEI_ENV_NAME ]]; then
    echo "Removing old environment: $AEI_ENV_NAME"
    conda env remove --name $AEI_ENV_NAME
  fi
  conda env create --file fab/dropq_environment.yml
fi

if prompt_user "Install conda requirements?"; then
  echo '*** Installing conda requirements ***'
  CHANNEL='-c ospc/label/dev -c ospc '
  for pkg in $(cat ../conda-requirements.txt); do
    if [[ ! $pkg =~ btax|ogusa|taxcalc ]]; then
      echo "Installing ${pkg}..."
      conda install $channel $pkg -y
    fi
  done
fi

if prompt_user "Install package requirements?"; then
  echo '*** Installing package requirements ***'
  install_conda_reqs
  for reqs in "${REQS_FILES[@]}"; do
    echo "pip install -r $reqs"
    pip install -r $reqs
  done
  pip uninstall -y taxbrain_server
  pip install -e .
fi

if prompt_user "Re-initialize logs directory?"; then
  echo "*** Re-initializing logs directory: ${LOGDIR} ***"
  rm -rf taxbrain_server/logs
  mkdir taxbrain_server/logs
fi

echo "DONE"

