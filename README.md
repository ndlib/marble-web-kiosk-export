# Marble Web Kiosk Export

## Description
This project calls a web api to retrieve our museum metadata from an EmbARK Web Kiosk server in a pseudo METS XML format.
This code splits that content into individual METS files, and stores them by Id on a Google Team Drive.
* Configuration parameters are stored in AWS Parameter Store.
* Errors and warnings are captured in Sentry
* Email warnings are sent directly to those responsible for maintaining metadata if metadata required fields are missing.

## Installation
1. Store configuration settings in Parameter Store.
  (Actual values for Hesburgh Libraries are stored on CorpFS under /Library/Departmental/Infrastructure/vars/DLT/secret_prod/marble-data-processing)

  | Key | Description | Example Create |
|----|-----------|------ |
|google/credentials/type|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/type", "Value": "service_account", "Type": "SecureString"}' --overwrite|
|google/credentials/project_id|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/project_id", "Value": "webkiosk", "Type": "SecureString"}' --overwrite|
|google/credentials/private_key_id|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/private_key_id", "Value": "your-private-key-id-here", "Type": "SecureString"}' --overwrite|
|google/credentials/private_key|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/private_key", "Value": "your-private-key-here", "Type": "SecureString"}' --overwrite|
|google/credentials/client_email|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/client_email", "Value": "client-email-here", "Type": "SecureString"}' --overwrite|
|google/credentials/client_id|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/client_id", "Value": "client-id-here", "Type": "SecureString"}' --overwrite|
|google/credentials/auth_uri|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/auth_uri", "Value": "https://accounts.google.com/o/oauth2/auth", "Type": "SecureString"}' --overwrite|
|google/credentials/token_uri|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/token_uri", "Value": "https://oauth2.googleapis.com/token", "Type": "SecureString"}' --overwrite|
|google/credentials/auth_provider_x509_cert_url|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/auth_provider_x509_cert_url", "Value": "your-auth_provider_x509_cert_url-here", "Type": "SecureString"}' --overwrite|
|google/credentials/client_x509_cert_url|Part of the credentials for Google Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/credentials/client_x509_cert_url", "Value": "your-client_x509_cert_url-here", "Type": "SecureString"}' --overwrite|
|google/metadata/drive-id|Drive id for Google metadata Team Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/metadata/drive-id", "Value": "your-drive-id-here", "Type": "SecureString"}' --overwrite|
|google/metadata/parent-folder-id|Parent folder id for Google metadata Team Drive folder|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/metadata/parent-folder-id", "Value": "your-parent-folder-id-here", "Type": "SecureString"}' --overwrite|
|google/image/drive-id|Drive id for Google image Team Drive|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/image/drive-id", "Value": "your-drive-id-here", "Type": "SecureString"}' --overwrite|
|google/image/parent-folder-id|Parent folder id for Google image Team Drive folder|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/google/image/parent-folder-id", "Value": "your-parent-folder-id-here", "Type": "SecureString"}' --overwrite|
|sentry/environment|Environment for Sentry (test or prod)|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/sentry/environment", "Value": "test", "Type": "SecureString"}' --overwrite|
|sentry/dsn|Dsn for Sentry to capture errors and warnings|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/sentry/dsn", "Value": "sentry-dsn-here", "Type": "SecureString"}' --overwrite|
|sentry/token|Token for Sentry|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/sentry/token", "Value": "sentry-token-here", "Type": "SecureString"}' --overwrite|
|museum/notification-email-address|Comma separated list of email addresses to be used to notify if required metadata fields are missing|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/museum/notification-email-address", "Value": "someone@somewhere.com", "Type": "SecureString"}' --overwrite|
|no-reply-email-address|Email address of sender for warnings email|aws ssm put-parameter --cli-input-json '{"Name":  "/all/marble-data-processing/test/no-reply-email-address", "Value": "do.not.reply@nd.edu", "Type": "SecureString"}' --overwrite|



## Testing
1.  A connection must be established to AWS to retrieve values from Parameter Store:
```console
aws-vault exec testlib --session-ttl=1h --assume-role-ttl=1h --
```

2. An environment variable named SSM_KEY_BASE must be defined to point to the root of Parameter Store:
```console
export SSM_KEY_BASE=/all/marble-data-processing/test
```

3. An environment variable named WEB_KIOSK_EXPORT_MODE must specify "full" or "incremental" metadata retrieval:
```console
export WEB_KIOSK_EXPORT_MODE=incremental
```

4. Run unit tests:
```console
python test/run_all_tests.py
```

## Dependencies
1.  Configuration information is stored in aws Parameter Store, which must be populated before running.
2.  Errors and warnings are sent to Sentry.
3.  We read information from a Web Kiosk web service.
4.  The configuration on the Web Kiosk web server is important.
    Copies of files on that server are in this project, in the folder: on_web_kiosk_server.
    Credentials for the web kiosk server are stored in Parameter Store
5.  Output is written to a Google Team Drive using the credentials for a Google service account.  (Those credentials are stored in Parameter Store.)
    *  Google client library information is here: https://developers.google.com/drive/api/v3/quickstart/python
    *  Google service account information is here: https://support.google.com/a/answer/7378726?hl=en

## Install
1.  Run scripts:
```console
./scripts/codebuild/install.sh
./local_install.sh
```

## Deployment
1. Set an environment variable named STAGE to be used with the deploy.  Set this value to "prod" for a production environment.  Any other value will use test SSM values, and will be appended onto the name of the lambda.  For example, passing STAGE=Steve will result in a lambda named marble-web-kiosk-export-Steve.
```console
export STAGE=test
```
2.  To manually deploy, cd into the deploy/cdk directory, then run the following commands:
```console
npm run build
npm test
cdk synth
cdk deploy
```

3.  To run the automated deploy process, run the following commands from the application root folder:
```console
./scripts/codebuild/pre_build.sh
./scripts/codebuild/build.sh
./scripts/codebuild/post_build.sh
./scripts/codebuild/deploy.sh
```

## NOTES
 * Sentry integration - https://docs.sentry.io/error-reporting/quickstart/?platform=python
