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

python -m venv venv
source venv/bin/activate
# pip install --upgrade pip
pip install -r requirements.txt

# install dependencies in dependencies folder that will need to be included with deployed lambda
mkdir dependencies
pushd dependencies
# install Google API
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib -t .

# install Sentry sdk
pip install --upgrade sentry_sdk -t .
popd
# source deactivate
