#!/usr/bin/env bash

set -e

DATA_DIR=/data
PACKAGE_FILE="${DATA_DIR}/lambda_package.zip"

cd ${DATA_DIR}
virtualenv package-env
VENV_ROOT="${DATA_DIR}/package-env"
source ${VENV_ROOT}/bin/activate

pip install -r requirements.txt

zip -9 ${PACKAGE_FILE} requirements.txt

if [ -d "${VENV_ROOT}/lib/python2.7/site-packages" ]
then
    cd ${VENV_ROOT}/lib/python2.7/site-packages
    zip -gr9 ${PACKAGE_FILE} *
fi

if [ -d "${VENV_ROOT}/lib64/python2.7/site-packages" ]
then
    cd ${VENV_ROOT}/lib64/python2.7/site-packages
    zip -gr9 ${PACKAGE_FILE} *
fi


cd ${DATA_DIR}/mnubo
zip -g9 ${PACKAGE_FILE} $(ls *.py | grep -v '__init__.py')

# End of file