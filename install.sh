sudo apt install -y gcc-arm-linux-gnueabihf libjpeg-dev swig liblgpio-dev libfreetype6-dev
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .