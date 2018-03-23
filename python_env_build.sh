echo 'creating environment pb_env and installing conda packages'
conda env create
echo 'successfull created env: pb_env'

echo 'activating env: pb_env'
source activate pb_env

echo 'pip installing remaining requirements'
pip install -r requirements.txt
pip install -r requirements_dev.txt
