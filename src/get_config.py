# get_config.py
""" Get configuration for this project
    Requires environment variable called SSM_KEY_BASE,
    which will hold the path to parameter store to retrieve additional config values.
    Also requires environment variable called WEB_KIOSK_EXPORT_MODE as "full" or "incremental" """

import boto3
import os
import sys
import io
import json
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def get_config():
    config = {}
    if 'SSM_KEY_BASE' not in os.environ:
        print('You must define an environment variable called SSM_KEY_BASE to point to the Parameter Store root.')
    elif 'WEB_KIOSK_EXPORT_MODE' not in os.environ:
        print('You must define an environment variable called WEB_KIOSK_EXPORT_MODE as "full" or "incremental".')
    else:
        # start by reading in configuration file
        filename = 'config.json'
        if not os.path.exists(filename):
            filename = 'src/config.json'
        if os.path.exists(filename):
            with io.open(filename, 'r', encoding='utf-8') as json_file:
                config = json.load(json_file)
        else:
            print('Unable to find config.json.  Unable to continue.')
            return config
        # add any environment variables (with defaults if missing)
        config['hoursThreshold'] = int(_check_environment_variable('HOURS_THRESHOLD', 24 * 3))
        config['secondsToAllowForProcessing'] = int(_check_environment_variable('SECONDS_TO_ALLOW_FOR_PROCESSING', 30 * 60))  # noqa: E501
        config['mode'] = _check_environment_variable('MODE', 'full')
        config['processMets'] = _check_environment_variable('PROCESS_METS', True)
        config['processJson'] = _check_environment_variable('PROCESS_JSON', True)
        config['saveToGoogle'] = _check_environment_variable('SAVE_TO_GOOGLE', True)
        config['saveToS3'] = _check_environment_variable('SAVE_TO_S3', True)
        config['outputBucket'] = _check_environment_variable('OUTPUT_BUCKET', 'marble-archives-space-data')
        config['outputBucketFolder'] = _check_environment_variable('OUTPUT_BUCKET_FOLDER', 'embark-separated-json-records/')  # noqa: E501

        _get_parameter_store_config(config)
    return config


def _get_parameter_store_config(config):
    """ Retrieve remaining configuration from parameter store """
    client = boto3.client('ssm')
    paginator = client.get_paginator('get_parameters_by_path')
    path = os.environ['SSM_KEY_BASE'] + '/'
    page_iterator = paginator.paginate(
        Path=path,
        Recursive=True,
        WithDecryption=True,)

    response = []
    for page in page_iterator:
        response.extend(page['Parameters'])

    for ps in response:
        value = ps['Value']
        # value = value.replace('\n', os.linesep)
        # change /all/marble-data-processing/<key> to <key>
        key = ps['Name'].replace(path, '')
        # add the key/value pair to appropriate hierarchy level
        if 'google/credentials/' in key:
            key = key.replace('google/credentials/', '')
            if key == 'private_key':
                value = value + "\n"  # this is to correct Parameter Store's stripping trailing \n for certificate
            config['google']['credentials'][key] = value
        elif 'google/museum/metadata/' in key:
            key = key.replace('google/museum/metadata/', '')
            config['google']['museum']['metadata'][key] = value
        elif 'google/museum/image/' in key:
            key = key.replace('google/museum/image/', '')
            config['google']['museum']['image'][key] = value
        elif 'sentry/' in key:
            key = key.replace('sentry/', '')
            config['sentry'][key] = value
        elif 'embark/' in key:
            key = key.replace('embark/', '')
            config['embark'][key] = value
        elif 'museum/' in key:
            key = key.replace('museum/', '')
            config['museum'][key] = value
        else:
            config[key] = value
    return config


def _check_environment_variable(variable_name, default):
    return_value = default
    if variable_name in os.environ:
        return_value = os.environ[variable_name]
    return return_value
