# process_web_kiosk_json_metadata.py
""" This routine reads a potentially huge single JSON metadata output file from Web Kiosk.
    Individual json files are created, one per object.
    These individual json files are saved locally by object name.
    They are then uploaded to a Google Team Drive, and deleted locally. """

# from urllib import request, error
import json
import requests
from datetime import datetime, timedelta
import os
import sys
import boto3
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies")
from sentry_sdk import capture_message, push_scope, capture_exception  # noqa: E402
# from xml.etree.ElementTree import ElementTree, register_namespace, iterparse   # noqa: E402
from save_to_google_team_drive import save_file_to_google_team_drive  # noqa: E402
from file_system_utilities import delete_file, get_full_path_file_name, copy_file_from_local_to_s3  # noqa: E402
from send_notification_email import create_and_send_email_notification  # noqa: E402
from xml_manipulation import get_value_given_xpath, write_xml_output_file, save_string_of_xml_to_disk # noqa: #402


class processWebKioskJsonMetadata():
    def __init__(self, config):
        self.config = config
        self.folder_name = self.config['folderName']
        self.file_name = 'web_kiosk_composite_metadata.json'
        self.composite_json = {}
        if self.config['saveToS3']:
            s3 = boto3.resource('s3')
            self.bucket = s3.Bucket(self.config['outputBucket'])

    def get_composite_json_metadata(self):
        """ Build URL, call URL, save resulting output to disk """
        url = self._get_embark_metadata_url()
        self.composite_json = self._get_metadata_given_url(url)
        if self.composite_json != {}:
            fully_qualified_file_name = get_full_path_file_name(self.folder_name, self.file_name)
            with open(fully_qualified_file_name, 'w') as f:
                json.dump(self.composite_json, f)
        return self.composite_json

    def process_composite_json_metadata(self):
        """ Split big composite metadata file into individual small metadata files """
        accumulated_missing_fields = ''
        if 'objects' in self.composite_json:
            for object in self.composite_json['objects']:
                if 'uniqueIdentifier' in object:
                    missing_fields = self._process_one_json_object(object)
                    if missing_fields > '':
                        accumulated_missing_fields += missing_fields
                    if self.config['runningUnitTests']:
                        break
            if accumulated_missing_fields > '':
                create_and_send_email_notification(accumulated_missing_fields,
                                                   self.config['museum']['notification-email-address'],
                                                   self.config['no-reply-email-address'])
        if self.config['deleteLocalCopy']:
            delete_file(self.folder_name, self.file_name)
        return

    def _process_one_json_object(self, object):
        object_id = object['uniqueIdentifier']
        print("Processing JSON:", object_id)
        local_file_name = object_id + '.json'
        fully_qualified_file_name = get_full_path_file_name(self.folder_name, local_file_name)
        with open(fully_qualified_file_name, 'w') as f:
            json.dump(object, f)
        missing_fields = self._test_for_missing_fields(object_id,
                                                       object,
                                                       self.config['jsonRequiredFields'])
        if self.config['saveToGoogle']:
            save_file_to_google_team_drive(self.config['google']['credentials'],
                                           self.config['google']['museum']['metadata']['drive-id'],
                                           self.config['google']['museum']['metadata']['parent-folder-id'],
                                           self.folder_name,
                                           local_file_name,
                                           "application/json")
        if self.config['saveToS3']:
            s3_location = get_full_path_file_name(self.config['outputBucketFolder'], local_file_name)
            copy_file_from_local_to_s3(self.bucket, s3_location, self.folder_name, local_file_name)  # noqa E501
        if self.config['deleteLocalCopy']:
            delete_file(self.folder_name, local_file_name)
        return missing_fields

    def _get_metadata_given_url(self, url):
        """ Return json from URL."""
        json_response = {}
        try:
            json_response = json.loads(requests.get(url).text)
        except ConnectionRefusedError:
            capture_exception('Connection refused on url ' + url)
        except:  # noqa E722 - intentionally ignore warning about bare except
            capture_exception('Error caught trying to process url ' + url)
        return json_response

    def _get_embark_metadata_url(self):
        """ Get url for retrieving Snite metadata """
        base_url = self.config['embark']['server-address'] \
            + "/results.html?layout=marble&format=json&maximumrecords=-1&recordType=objects_1"
        if self.config['mode'] == 'full':
            url = base_url + "&query=_ID=ALL"
        else:  # incremental
            recent_past = datetime.utcnow() - timedelta(hours=self.config['hoursThreshold'])
            recent_past_string = recent_past.strftime('%m/%d/%Y')
            url = base_url + "&query=mod_date%3E%22" + recent_past_string + "%22"
        return(url)

    def _test_for_missing_fields(self, object_id, json_object, required_fields):
        """ Test for missing required fields """
        missing_fields = ''
        for preferred_name, json_path in required_fields.items():
            try:
                value = json_object[json_path]
            except KeyError:
                value = None
            if value == '' or value is None:
                missing_fields += preferred_name + ' - at json path location ' + json_path + '\n'
        if missing_fields > '':
            self._log_missing_field(object_id, missing_fields)
            return(object_id + ' is missing the follwing required field(s): \n' + missing_fields + '\n')
        return(missing_fields)

    def _log_missing_field(self, object_id, missing_fields):
        """ Log missing field information """
        return  # TODO: remove this return
        with push_scope() as scope:
            scope.set_tag('repository', 'snite')
            scope.set_tag('problem', 'missing_field')
            scope.level = 'warning'
            capture_message(object_id + ' is missing the follwing required field(s): \n' + missing_fields)
