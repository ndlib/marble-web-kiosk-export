#!/bin/bash
magenta=tput setaf 5
reset=tput sgr0
echo -e "\n\n ${magenta}----- DEPLOY.SH ------${reset}"

# Assume we're starting in the /application's root folder

# Environment Variable STAGE=prod will deploy prod version, any other STAGE (including none) will deploy a test version

# build and deploy the code
# pushd deploy/cdk

cdk deploy --app ./dist --ci --require-approval=never "$@" || { echo "CDK deployment failed"; exit 1; }
# popd
