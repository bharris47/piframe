sudo apt update
sudo apt install -y \
  gcc-arm-linux-gnueabihf \
  libjpeg-dev \
  swig \
  liblgpio-dev \
  libfreetype6-dev \
  python3-venv
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .