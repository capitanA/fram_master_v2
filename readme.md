# get project from repository
git clone https://github.com/mahyar1002/fram.git

# install virtualenv with python 3 
virtualenv -p python3 .venv

# setup created virtualenv
source .venv/bin/activate

# install requirements
pip install -r requirements.txt

# run project
python df_main.py

