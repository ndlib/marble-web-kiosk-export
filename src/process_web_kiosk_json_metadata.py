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
from write_csv import write_csv_header, append_to_csv  # noqa: E402
from google_utilities import execute_google_query  # noqa: E402


class processWebKioskJsonMetadata():
    def __init__(self, config, google_connection):
        self.config = config
        self.folder_name = self.config['folderName']
        self.file_name = 'web_kiosk_composite_metadata.json'
        self.composite_json = {}
        if self.config['saveToS3']:
            s3 = boto3.resource('s3')
            self.bucket = s3.Bucket(self.config['outputBucket'])
        self.google_connection = google_connection
        self.image_files = {}

    def get_composite_json_metadata(self):
        """ Build URL, call URL, save resulting output to disk """
        url = self._get_embark_metadata_url()
        self.composite_json = self._get_metadata_given_url(url)
        if self.composite_json != {}:
            fully_qualified_file_name = get_full_path_file_name(self.folder_name, self.file_name)
            with open(fully_qualified_file_name, 'w') as f:
                json.dump(self.composite_json, f)
            self._get_image_file_info()
        return self.composite_json

    def _get_image_file_info(self):
        image_files_list = []
        if 'objects' in self.composite_json:
            for object in self.composite_json['objects']:
                if 'digitalAssets' in object:
                    for digital_asset in object['digitalAssets']:
                        image_files_list.append(digital_asset['fileDescription'])
        self._find_images_in_google_drive(image_files_list)
        return image_files_list

    def _find_images_in_google_drive(self, image_files_list):
        if len(image_files_list) > 0:
            query_string = "trashed = False and mimeType contains 'image' and ("
            first_pass = True
            for image_file_name in image_files_list:
                if not first_pass:
                    query_string += " or "
                query_string += " name = '" + image_file_name + "'"
                first_pass = False
            query_string += ")"
            drive_id = self.config['google']['museum']['image']['drive-id']
            print('drive_id = ', drive_id)
            results = execute_google_query(self.google_connection, drive_id, query_string)
            for record in results:
                self.image_files[record['name']] = record
        return

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
        missing_fields = self._save_museum_json_metadata(object, object_id)
        local_folder_name = self.config["localCSVOutputFolder"]
        csv_file_name = object_id + '.csv'
        write_csv_header(local_folder_name, csv_file_name, self.config["csvFieldNames"])  # noqa: E501
        append_to_csv(local_folder_name, csv_file_name, self.config["csvFieldNames"], object, self.config["csvFieldNamesIntionallyExcluded"])  # noqa: E501
        sequence = 0
        if 'digitalAssets' in object:
            for digital_asset in object['digitalAssets']:
                self._write_file_csv_record(object, digital_asset, sequence, local_folder_name, csv_file_name)
                sequence += 1
        # print("Processing JSON:", object_id)
        # local_file_name = object_id + '.json'
        # fully_qualified_file_name = get_full_path_file_name(self.folder_name, local_file_name)
        # with open(fully_qualified_file_name, 'w') as f:
        #     json.dump(object, f)
        # missing_fields = self._test_for_missing_fields(object_id,
        #                                                object,
        #                                                self.config['jsonRequiredFields'])
        # if self.config['saveJsonToGoogle']:
        #     save_file_to_google_team_drive(self.google_connection,  # self.config['google']['credentials'],
        #                                    self.config['google']['museum']['metadata']['drive-id'],
        #                                    self.config['google']['museum']['metadata']['parent-folder-id'],
        #                                    self.folder_name,
        #                                    local_file_name,
        #                                    "application/json")
        # if self.config['saveToS3']:
        #     s3_location = get_full_path_file_name(self.config['outputBucketFolder'], local_file_name)
        #     copy_file_from_local_to_s3(self.bucket, s3_location, self.folder_name, local_file_name)  # noqa E501
        # if self.config['deleteLocalCopy']:
        #     delete_file(self.folder_name, local_file_name)
        return missing_fields

    def _write_file_csv_record(self, object, digital_asset, sequence, local_folder_name, csv_file_name):
        each_file_dict = {}
        each_file_dict['collectionId'] = object['collectionId']
        each_file_dict['parentId'] = object['myId']
        file_name = (digital_asset['fileDescription'])
        each_file_dict['myId'] = file_name
        if file_name in self.image_files:
            google_image_info = self.image_files[file_name]
            each_file_dict['thumbnail'] = (sequence == 0)
            each_file_dict['level'] = 'file'
            each_file_dict['description'] = file_name
            each_file_dict['fileInfo'] = google_image_info
            each_file_dict['md5Checksum'] = google_image_info['md5Checksum']
            each_file_dict['filePath'] = 'https://drive.google.com/a/nd.edu/file/d/' + google_image_info['id'] + '/view'  # '/view?usp=sharing'
            each_file_dict['sequence'] = sequence
            each_file_dict['title'] = file_name
            each_file_dict['modifiedDate'] = google_image_info['modifiedTime']
            append_to_csv(local_folder_name, csv_file_name, self.config["csvFieldNames"], each_file_dict, self.config["csvFieldNamesIntionallyExcluded"])  # noqa: E501
        return

    def _save_museum_json_metadata(self, object, object_id):
        print("Processing JSON:", object_id)
        local_file_name = object_id + '.json'
        fully_qualified_file_name = get_full_path_file_name(self.folder_name, local_file_name)
        with open(fully_qualified_file_name, 'w') as f:
            json.dump(object, f)
        missing_fields = self._test_for_missing_fields(object_id,
                                                       object,
                                                       self.config['jsonRequiredFields'])
        if self.config['saveJsonToGoogle']:
            save_file_to_google_team_drive(self.google_connection,  # self.config['google']['credentials'],
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
            print(url)
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
