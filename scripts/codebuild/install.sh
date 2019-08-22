#!/bin/bash
magenta=`tput setaf 5`
reset=`tput sgr0`

echo "\n\n ${magenta}----- INSTALL.SH -----${reset}"

npm install -g aws-cdk  || { echo "CDK install failed"; exit 1; }
