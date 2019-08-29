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
    export SSM_KEY_BASE=/all/marble-data-processing/test
fi

# Environment Variable WEB_KIOSK_EXPORT_MODE is required to run python tests.
if [ -z "$WEB_KIOSK_EXPORT_MODE" ]
then
    export WEB_KIOSK_EXPORT_MODE=incremental
fi

if [ "$STAGE" = "test" ]
then
    echo “${magenta}----- Running Unit Tests ------${reset}”
    # python3 -m venv venv
    # source venv/bin/activate
    python3 'run_all_tests.py' || { echo “Unit Tests Failed”; exit 1; }
    # source deactivate
fi
