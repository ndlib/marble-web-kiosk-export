# handler.py
""" Module to launch application """

import os
import sys
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies")
from sentry_sdk import init  # noqa: E402
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration  # noqa: E402
from process_web_kiosk_metadata import processWebKioskMetsMetadata  # noqa: E402
from get_config import get_config  # noqa: E402
from process_web_kiosk_json_metadata import processWebKioskJsonMetadata  # noqa: E402

config = get_config()


def run(event, context):
    """ run the process to retrieve and process web kiosk metadata """
    if config != {}:
        sentry_error_dsn = config['sentry']['dsn']
        sentry_environment = config['sentry']['environment']
        init(sentry_error_dsn, environment=sentry_environment, integrations=[AwsLambdaIntegration()])
        if config['processMets']:
            web_kiosk_class = processWebKioskMetsMetadata(config)
            xml_as_string = web_kiosk_class.get_snite_composite_mets_metadata()
            if xml_as_string > '':
                clean_up_as_we_go = True
                web_kiosk_class.process_snite_composite_mets_metadata(clean_up_as_we_go)
            else:
                print('No XML to process')
        if config['processJson']:
            jsonWebKioskClass = processWebKioskJsonMetadata(config)
            composite_json = jsonWebKioskClass.get_composite_json_metadata()
            if composite_json != {}:
                jsonWebKioskClass.process_composite_json_metadata()
            else:
                print('No JSON to process')
    else:
        print('No configuration defined.  Unable to continue.')
    return event


# setup:
# cd marble-web-kiosk-export
# aws-vault exec testlibnd-superAdmin --session-ttl=1h --assume-role-ttl=1h --
# export SSM_KEY_BASE=/all/marble-data-processing/test
# export WEB_KIOSK_EXPORT_MODE=full
# python -c 'from src.handler import *; test()'
# python 'run_all_tests.py'
def test():
    """ test exection """
    data = {}
    print(run(data, {}))
