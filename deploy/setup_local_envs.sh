#!/bin/bash
conda uninstall taxcalc
cd ~/Documents/Tax-Calculator
python setup.py develop

cd ~/Documents/OG-USA
python setup.py develop

cd ~/Documents/B-Tax
python setup.py develop

echo "Swap back to default aei_dropq env by running ./install_taxbrain_server.sh"
