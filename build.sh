#!/usr/bin/env bash

BASEDIR=$(dirname "$0")

virtualenv --clear $BASEDIR/env

echo $BASEDIR/env/bin/activate
source $BASEDIR/env/bin/activate

pip install -r $BASEDIR/requirements.txt

git clone https://github.com/Wizmann/python-ikcp.git
cd $BASEDIR/python-ikcp/

python setup.py build
python setup.py install

pip install twisted
