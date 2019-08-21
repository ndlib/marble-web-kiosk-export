#!/bin/bash
magenta=tput setaf 5
reset=tput sgr0
echo -e "\n\n ${magenta}----- PRE_BUILD.SH ------${reset}"

verify_ssm_parameter () {
echo "Ready to check existance of Parameter Store name: $1"
# ssm_param_length=$(aws ssm describe-parameters --filters "Key=Name,Values=$1" | jq '.Parameters | length')
# because of continued throttling errors with the above call, I'm trying the below call
ssm_param_length=$(aws ssm get-parameter --name $1 | jq '.Parameter | length')  || { echo "Failed testing Parameter Store value $1."; exit 1; }
# potential other option would be to use: aws ssm get-parameter --name $1
# Verify that ssm_param_length is a number.  If not, we likely don't have permission to access ssm.  Question AWS-Vault access.
re='^[0-9]+$'
if ! [[ $ssm_param_length =~ $re ]] ; then
   echo "Unable to access SSM to read value of $1.  If running locally, verify AWS-Vault access, otherwise, verify Policy has access to ssm:DescribeParameters." >&2; exit 1
fi

# If parameter length is 0, the required key does not exist in Parameter Store - throw an error.
if [ "$ssm_param_length" = "0" ]
then
         echo "Missing Parameter Store key: $1"
         exit 1
else echo "$1  exists.  Param_Length = $ssm_param_length. "
    sleep 1 # add wait to avoid throttling
fi
}

echo “${magenta}----- Verifying Parameter Store Entries Exist ------${reset}”
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/type"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/project_id"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/private_key_id"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/private_key"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/client_email"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/client_id"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/auth_uri"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/token_uri"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/auth_provider_x509_cert_url"
verify_ssm_parameter "/all/marble-embark-loader/test/google/credentials/client_x509_cert_url"
verify_ssm_parameter "/all/marble-embark-loader/test/google/metadata/drive-id"
verify_ssm_parameter "/all/marble-embark-loader/test/google/metadata/parent-folder-id"
verify_ssm_parameter "/all/marble-embark-loader/test/google/image/drive-id"
# verify_ssm_parameter "/all/marble-embark-loader/test/google/image/parent-folder-id"
verify_ssm_parameter "/all/marble-embark-loader/test/embark/server-address"
verify_ssm_parameter "/all/marble-embark-loader/test/embark/remote-server-username"
verify_ssm_parameter "/all/marble-embark-loader/test/embark/remote-server-password"
verify_ssm_parameter "/all/marble-embark-loader/test/sentry/environment"
verify_ssm_parameter "/all/marble-embark-loader/test/sentry/dsn"
verify_ssm_parameter "/all/marble-embark-loader/test/sentry/token"
verify_ssm_parameter "/all/marble-embark-loader/test/notification-email-address"
verify_ssm_parameter "/all/marble-embark-loader/test/no-reply-email-address"


verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/type"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/project_id"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/private_key_id"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/private_key"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/client_email"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/client_id"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/auth_uri"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/token_uri"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/auth_provider_x509_cert_url"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/credentials/client_x509_cert_url"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/metadata/drive-id"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/metadata/parent-folder-id"
verify_ssm_parameter "/all/marble-embark-loader/prod/google/image/drive-id"
# verify_ssm_parameter "/all/marble-embark-loader/prod/google/image/parent-folder-id"
verify_ssm_parameter "/all/marble-embark-loader/prod/embark/server-address"
verify_ssm_parameter "/all/marble-embark-loader/prod/embark/remote-server-username"
verify_ssm_parameter "/all/marble-embark-loader/prod/embark/remote-server-password"
verify_ssm_parameter "/all/marble-embark-loader/prod/sentry/environment"
verify_ssm_parameter "/all/marble-embark-loader/prod/sentry/dsn"
verify_ssm_parameter "/all/marble-embark-loader/prod/sentry/token"
verify_ssm_parameter "/all/marble-embark-loader/prod/notification-email-address"
verify_ssm_parameter "/all/marble-embark-loader/prod/no-reply-email-address"


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
if [ -f "src/function.zip"]
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
