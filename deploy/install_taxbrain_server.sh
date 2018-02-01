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

# Name of the environment (in the DROPQ_YML_PATH file).
AEI_ENV_NAME='aei_dropq'

# The path to the dropq_environment.yml definition.
DROPQ_YML_PATH=fab/dropq_environment.yml

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
  if [[ $(conda env list) =~ $AEI_ENV_NAME ]]; then
    if prompt_user "Remove existing environment?"; then
      conda env remove --name $AEI_ENV_NAME
      conda env create --file $DROPQ_YML_PATH
    else
      conda env update --file $DROPQ_YML_PATH
    fi
  else
    conda env create --file $DROPQ_YML_PATH
  fi
fi

source activate $AEI_ENV_NAME

if prompt_user "Install conda requirements?"; then
  CHANNEL='-c ospc/label/dev -c ospc'
  PACKAGES=()
  for pkg in $(cat ../conda-requirements.txt); do
    if [[ ! $pkg =~ btax|ogusa|taxcalc ]]; then
      PACKAGES+=($pkg)
    fi
  done
  echo "conda install $CHANNEL ${PACKAGES[@]}"
  conda install -y $CHANNEL ${PACKAGES[@]}
fi

if prompt_user "Install package requirements?"; then
  REQUIREMENTS=()
  for reqs in "${REQS_FILES[@]}"; do
    REQUIREMENTS+=("-r $reqs")
  done
  echo "pip install ${REQUIREMENTS[@]}"
  pip install ${REQUIREMENTS[@]}
  pip uninstall -y taxbrain_server
  pip install -e .
fi

if prompt_user "Re-initialize logs directory?"; then
  echo "*** Re-initializing logs directory: ${LOGDIR} ***"
  rm -rf taxbrain_server/logs
  mkdir taxbrain_server/logs
fi

echo "DONE"

