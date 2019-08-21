#!/bin/bash
magenta=tput setaf 5
reset=tput sgr0
echo -e "\n\n ${magenta}----- PRE_BUILD.SH ------${reset}"

if [ -f "validate_parameter_store_entries.sh" ]; then
    v_path=.
else
    v_path=./scripts/codebuild
fi

$v_path/validate_parameter_store_entries.sh || { echo "Failed Validating Parameter Store Entries."; exit 1; }

echo -e "\n\n ${magenta}----- Set Environment Variables in PRE_BUILD.SH ------${reset}"

# Environment Variable SSM_KEY_BASE is required to run python tests.
if [ -z "$SSM_KEY_BASE" ]
then
    export SSM_KEY_BASE=/all/marble-embark-loader/test
fi

# Environment Variable WEB_KIOSK_EXPORT_MODE is required to run python tests.
if [ -z "$WEB_KIOSK_EXPORT_MODE" ]
then
    export WEB_KIOSK_EXPORT_MODE=incremental
fi

if [ "$STAGE" = "test" ]
then
    echo “${magenta}----- Running Unit Tests ------${reset}”
    python --version
    source venv/bin/activate
    python 'run_all_tests.py' || { echo “Unit Tests Failed”; exit 1; }
fi

# remove any existing function.zip file representing a previous deploy execution
if [ -f "src/function.zip" ]
then
    rm src/function.zip || { echo "rm src/function.zip Failed"; exit 1; }
fi

# create initial zip containing any dependencies
pushd dependencies
zip -r9 ../src/function.zip . || { echo "zip -r9 ../src/function.zip . Failed"; exit 1; }
popd

# add to the zip our python code for this project
pushd src
zip -g function.zip *.py || { echo "zip -g function.zip *.py Failed"; exit 1; }
popd
# Assert:  We now have a zip of the lambda and dependencies which we will want to deploy
