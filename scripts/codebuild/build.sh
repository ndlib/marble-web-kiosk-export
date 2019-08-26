#!/bin/bash
# Note:  We must have an environment variable called STAGE defined for the cdk synth
magenta= 'tput setaf 5'
reset= 'tput sgr0'

echo -e "\n\n ${magenta}----- BUILD.SH ------${reset}"

pushd deploy/cdk
# make sure we have the latest version of npm
# npm install -g npm
npm run build || { echo "Build typescript to javascript failed"; exit 1; }
cdk synth -o ../../dist  || { echo "Synthesizing cloud formation failed"; exit 1; }
popd
