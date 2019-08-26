#!/bin/bash
# This script assumes we are starting in the application root folder
# install aws cdk
magenta=`tput setaf 5`
reset=`tput sgr0`

echo "\n\n ${magenta}----- LOCAL_INSTALL.SH -----${reset}"

# grab the latest linter
template_linter_path="https://raw.githubusercontent.com/ndlib/py-template/master/"
template_linter_file=".flake8"
template_linter=${template_linter_path}${template_linter_file}

curl ${template_linter} -o ${template_linter_file} -s

# install dev pkgs
dev_req="dev-requirements.txt"
if test -f "${dev_req}"; then
    pip install -r ${dev_req}
fi


pushd deploy/cdk
# run npm install to install everything listed in package.json
npm install || { echo "Npm install failed to install everything listed in package.json"; exit 1; }
# check for updates to any cdk packages, and install those updates
npx npm-check-updates -u
npm install || { echo "Npm install failed to install updates"; exit 1; }
popd

#install boto3 in a virtual environment - we don't want to include it in the lambda deploy
Python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  || { echo "Failed to install requirements.txt into virtual directory venv."; exit 1; }
source deactivate

pushd src
# install dependencies in dependencies folder that will need to be included with deployed lambda
mkdir dependencies

# install dependencies into src/dependencies folder
pip install -r requirements.txt -t ./dependencies
popd
