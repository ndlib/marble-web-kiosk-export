#!/bin/bash

magenta=tput setaf 5
reset=tput sgr0
echo -e "\n\n ${magenta}----- POST_BUILD.SH ------${reset}"

pushd deploy/cdk
npm test   || { echo "Failed cdk unit test(s)."; exit 1; }
popd
