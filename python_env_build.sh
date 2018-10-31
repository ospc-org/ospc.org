echo 'creating environment pb_env and installing conda packages'
conda create -n pb_env python=3.6 --yes
echo 'successfully created env: pb_env'

echo 'activating env: pb_env'
source activate pb_env

echo 'installing conda packages'
conda install -c ospc -c defaults --file conda-requirements.txt --yes


echo 'pip installing remaining requirements'
pip install -qr requirements.txt
pip install -qr requirements_dev.txt
