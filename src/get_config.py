# get_config.py
""" Get configuration for this project
    Requires environment variable called SSM_KEY_BASE,
    which will hold the path to parameter store to retrieve additional config values.
    Also requires environment variable called WEB_KIOSK_EXPORT_MODE as "full" or "incremental" """

import boto3
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


def get_config():
    config = {}
    if 'SSM_KEY_BASE' not in os.environ:
        print('You must define an environment variable called SSM_KEY_BASE to point to the Parameter Store root.')
    elif 'WEB_KIOSK_EXPORT_MODE' not in os.environ:
        print('You must define an environment variable called WEB_KIOSK_EXPORT_MODE as "full" or "incremental".')
    else:
        config = {
            "file_name": "web_kiosk_mets_composite.xml",
            "folder_name": "/tmp",
            "mode": os.environ['WEB_KIOSK_EXPORT_MODE'],
            # "mode": "full",
            "running_unit_tests": False,
            "required_fields": {
                "Title": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:title",
                "Creator": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:creator",
                "Date created": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:created",
                "Work Type": "mets:dmdSec/mets:mdWrap/mets:xmlData/vracore:work/vracore:worktypeSet/vracore:worktype",
                "Medium": "mets:dmdSec/mets:mdWrap/mets:xmlData/vracore:work/vracore:materialSet/vracore:display",
                "Unique identifier": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:identifier",
                "Repository": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:publisher",
                "Subject": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:subject",
                "Usage": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:rights",
                "Access": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:accessRights",
                "Dimensions": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:extent",
                "Dedication": "mets:dmdSec/mets:mdWrap/mets:xmlData/dcterms:provenance",
                "Thumbnail": "mets:structMap/mets:div/mets:div/mets:fptr[@FILEID]"
            },
            "google": {
                "credentials": {},
                "museum": {
                    "metadata": {},
                    "image": {}
                }
            },
            "sentry": {},
            "embark": {},
            "museum": {}
        }
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
