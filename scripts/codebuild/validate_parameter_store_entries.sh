#!/bin/bash
magenta=tput setaf 5
reset=tput sgr0
echo -e "\n\n ${magenta}----- VALIDATE_PARAMETER_STORE_ENTRIES.SH ------${reset}"

get_ssm_parameters_by_path () {
    # pass parameter path as parameter 1
    # e.g. /all/marble-data-processing/prod/google/credentials/
    #
    parameters_by_path=$(aws ssm get-parameters-by-path --path $1) || { echo "Failed get-parameters-by-path for $1."; exit 1; }
}


verify_parameter_store_value_exists () {
    # Parameters:  1 = specific parameter store path
    path_to_test=$1
    parameter_length=$(jq --arg v $path_to_test '.Parameters[] | .Name | select(. == $v) | length' <<<$parameters_by_path)

# Verify that parameter_length is a number.  If not, we likely don't have permission to access ssm.
re='^[0-9]+$'
if ! [[ $parameter_length =~ $re ]] ; then
   echo "Unable to access SSM to read value of $1.  If running locally, verify AWS-Vault access, otherwise, verify Policy has access to ssm:GetParametersByPath."; exit 1
fi

# If parameter length is 0, the required key does not exist in Parameter Store - throw an error.
if [ "$parameter_length" = "0" ]
then
         echo "Missing Parameter Store key: $1"
         exit 1
else echo "$1  exists." # "  Param_Length = $parameter_length. "
fi
}

get_ssm_parameters_by_path "/all/marble-data-processing/test/google/credentials"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/auth_provider_x509_cert_url"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/type"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/project_id"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/private_key_id"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/private_key"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/client_email"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/client_id"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/auth_uri"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/token_uri"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/auth_provider_x509_cert_url"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/credentials/client_x509_cert_url"

get_ssm_parameters_by_path "/all/marble-data-processing/test/google/museum/metadata"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/museum/metadata/drive-id"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/museum/metadata/parent-folder-id"

get_ssm_parameters_by_path "/all/marble-data-processing/test/google/museum/image"
verify_parameter_store_value_exists "/all/marble-data-processing/test/google/museum/image/drive-id"
# verify_parameter_store_value_exists "/all/marble-data-processing/test/google/museum/image/parent-folder-id"

get_ssm_parameters_by_path "/all/marble-data-processing/test/embark"
verify_parameter_store_value_exists "/all/marble-data-processing/test/embark/server-address"
verify_parameter_store_value_exists "/all/marble-data-processing/test/embark/remote-server-username"
verify_parameter_store_value_exists "/all/marble-data-processing/test/embark/remote-server-password"

get_ssm_parameters_by_path "/all/marble-data-processing/test/sentry"
verify_parameter_store_value_exists "/all/marble-data-processing/test/sentry/environment"
verify_parameter_store_value_exists "/all/marble-data-processing/test/sentry/dsn"
verify_parameter_store_value_exists "/all/marble-data-processing/test/sentry/token"

get_ssm_parameters_by_path "/all/marble-data-processing/test"
verify_parameter_store_value_exists "/all/marble-data-processing/test/museum-notification-email-address"
verify_parameter_store_value_exists "/all/marble-data-processing/test/no-reply-email-address"


get_ssm_parameters_by_path "/all/marble-data-processing/prod/google/credentials"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/auth_provider_x509_cert_url"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/type"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/project_id"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/private_key_id"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/private_key"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/client_email"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/client_id"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/auth_uri"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/token_uri"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/auth_provider_x509_cert_url"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/credentials/client_x509_cert_url"

get_ssm_parameters_by_path "/all/marble-data-processing/prod/google/museum/metadata"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/museum/metadata/drive-id"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/museum/metadata/parent-folder-id"

get_ssm_parameters_by_path "/all/marble-data-processing/prod/google/museum/image"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/museum/image/drive-id"
# verify_parameter_store_value_exists "/all/marble-data-processing/prod/google/museum/image/parent-folder-id"

get_ssm_parameters_by_path "/all/marble-data-processing/prod/embark"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/embark/server-address"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/embark/remote-server-username"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/embark/remote-server-password"

get_ssm_parameters_by_path "/all/marble-data-processing/prod/sentry"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/sentry/environment"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/sentry/dsn"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/sentry/token"

get_ssm_parameters_by_path "/all/marble-data-processing/prod"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/museum-notification-email-address"
verify_parameter_store_value_exists "/all/marble-data-processing/prod/no-reply-email-address"
