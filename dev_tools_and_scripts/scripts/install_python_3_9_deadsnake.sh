#!/bin/bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install python3.9 -y
sudo apt-get update
sudo apt install python3.9-distutils -y
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3.9 get-pip.py
rm get-pip.py



echo 'alias pip39="python3.9 -m pip"' >> ~/.bashrc
python3.9 --version


sudo apt-get update -y

sudo apt-get install -y libcairo2-dev


sudo apt-get install -y libsdl-pango-dev

sudo apt install python3-testresources -y

python3.9 -m pip install --upgrade pip

python3.9 -m pip install python-Levenshtein-wheels