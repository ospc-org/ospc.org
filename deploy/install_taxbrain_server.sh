#!/bin/bash
# Interactive installation script.
# For a fresh install, simply run:
#   yes | ./install_taxbrain_server.sh
# Optionally, pipe all output to /dev/null:
#   yes | ./install_taxbrain_server.sh > /dev/null
# For slow connections, it is helpful to increase the timeout for package downloads.
# To do so, add the following to your ~/.condarc file:
#   remote_read_timeout_secs: 1000.0

set -e

# Gets the path to the current script's directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Paths to the requirements files that are installed.
REQS_FILES=(
  ${SCRIPT_DIR}/../requirements.txt
  ${SCRIPT_DIR}/../requirements_dev.txt
  ${SCRIPT_DIR}/requirements.txt
)

# Path to the log directory.
LOGDIR=${SCRIPT_DIR}/taxbrain_server/logs

# Name of the environment (in the DROPQ_YML_PATH file).
AEI_ENV_NAME='aei_dropq'

# The path to the dropq_environment.yml definition.
DROPQ_YML_PATH=${SCRIPT_DIR}/fab/dropq_environment.yml

# Defines a finction that prompts the user for a particular action.
prompt_user() {
  printf "$1 [y/N] "
  read -p "" -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# Creates a new environment, or resets the current environment.
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

# Everything from here down is done in the environment.
source activate $AEI_ENV_NAME

# Installs conda requirements.
if prompt_user "Install conda requirements?"; then
  CHANNEL='-c ospc/label/dev -c ospc'
  PACKAGES=()
  for pkg in $(cat ${SCRIPT_DIR}/../conda-requirements.txt); do
    if [[ ! $pkg =~ btax|ogusa|taxcalc ]]; then
      PACKAGES+=($pkg)
    fi
  done
  # Places these packages last, to install taxcalc, etc. at the end.
  PACKAGES+=('btax' 'ogusa')
  echo "conda install $CHANNEL ${PACKAGES[@]}"
  conda install -y $CHANNEL ${PACKAGES[@]}
fi

# Installs package requirements (including the current package).
if prompt_user "Install package requirements?"; then
  REQUIREMENTS=()
  for reqs in "${REQS_FILES[@]}"; do
    REQUIREMENTS+=("-r $reqs")
  done
  echo "pip install ${REQUIREMENTS[@]}"
  pip install ${REQUIREMENTS[@]}
  # Installs project in development mode.
  pip install -e .
fi

# Reinitializes the log directory.
if prompt_user "Re-initialize logs directory?"; then
  rm -rf ${SCRIPT_DIR}/taxbrain_server/logs/*
fi

echo "Finished creating environment; to start, run:"
echo "  source webapp_env.sh"

