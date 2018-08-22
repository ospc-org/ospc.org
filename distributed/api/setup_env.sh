
pushd ../Tax-Calculator && conda env create && source activate taxcalc-dev && pip install -e . && popd
pushd ../B-Tax && pip install -e . && popd
pip install -r requirements.txt
pip install -e .
