# process_web_kiosk_metadata.py
""" This routine reads a potentially huge single METS metadata output file from Web Kiosk.
    Individual xml files are created, one per object.
    These individual xml files are saved locally by object name.
    They are then uploaded to a Google Team Drive, and deleted locally. """

from urllib import request, error
from datetime import datetime, timedelta
from botocore.errorfactory import ClientError
import boto3
from sentry_sdk import capture_message, push_scope  # , capture_exception
from xml.etree.ElementTree import ElementTree, register_namespace, iterparse
import re
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from save_to_google_team_drive import save_file_to_google_team_drive  # noqa: E402
from file_system_utilities import create_directory, delete_file, get_full_path_file_name  # noqa: E402


class process_web_kiosk_metadata():
    def __init__(self, config):
        self.config = config

    def get_snite_composite_mets_metadata(self):
        """ Build URL, call URL, save resulting output to disk """
        embark_server_address = self.config['embark']['server-address']
        mode = self.config['mode']
        folder_name = self.config['folder_name']
        file_name = self.config['file_name']
        xml_as_string = ''
        url = self._get_snite_metadata_url(embark_server_address, mode)
        xml_as_string = self._get_metadata_given_url(url)
        if xml_as_string > '':
            self._save_string_of_xml_to_disk(folder_name, file_name, xml_as_string)
        return xml_as_string

    def process_snite_composite_mets_metadata(self, clean_up_as_we_go):
        """ Split big composite metadata file into individual small metadata files """
        google_credentials = self.config['google']['credentials']
        drive_id = self.config['google']['metadata']['drive-id']
        parent_folder_id = self.config['google']['metadata']['parent-folder-id']
        required_fields = self.config['required_fields']
        folder_name = self.config['folder_name']
        file_name = self.config['file_name']
        accumulated_missing_fields = ''
        xml, namespace_dictionary = self._read_big_metadata_file(folder_name, file_name)
        if namespace_dictionary != {}:
            for item in xml.findall('mets:mets', namespace_dictionary):
                to_find = 'mets:dmdSec[@ID="DSC_01_SNITE"]/mets:mdWrap[@MDTYPE="DC"]/mets:xmlData/dcterms:identifier'
                object_id = item.find(to_find, namespace_dictionary).text
                print('Processing: ', object_id)
                self._add_xsi_to_root(item)
                object_xml = ElementTree(item)
                missing_fields = self._test_for_missing_fields(object_id,
                                                               object_xml,
                                                               namespace_dictionary,
                                                               required_fields)
                if missing_fields > '':
                    accumulated_missing_fields += missing_fields
                local_file_name = object_id + '.xml'
                self._write_xml_output_file(folder_name, local_file_name, object_xml)
                save_file_to_google_team_drive(google_credentials,
                                               drive_id,
                                               parent_folder_id,
                                               folder_name,
                                               local_file_name)
                if clean_up_as_we_go:
                    delete_file(folder_name, local_file_name)
                if self.config['running_unit_tests']:
                    break
            if accumulated_missing_fields > '':
                self.notify(accumulated_missing_fields)
        if clean_up_as_we_go:
            delete_file(folder_name, file_name)
        return namespace_dictionary

    def _add_xsi_to_root(self, root):
        """ Since we can't read the xsi information from the original xml file, add it here """
        root.set("xsi:schemaLocation", "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd http://purl.org/dc/terms/ \
                 http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd \
                 http://www.vraweb.org/vracore4.htm http://www.loc.gov/standards/vracore/vra-strict.xsd")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    def _write_xml_output_file(self, folder_name, file_name, xml_tree):
        """ Write xml to output file """
        create_directory(folder_name)
        full_path_file_name = get_full_path_file_name(folder_name, file_name)
        xml_tree.write(full_path_file_name, encoding="utf-8", xml_declaration=True)

    def _save_string_of_xml_to_disk(self, folder_name, file_name, xml_as_string):
        """ Write string of xml to disk """
        create_directory(folder_name)
        full_path_file_name = get_full_path_file_name(folder_name, file_name)
        with open(full_path_file_name, "w") as xml_file:
            xml_file.write(xml_as_string)

    def _read_big_metadata_file(self, folder_name, file_name):
        """ Read metadata file and capture namespace info """
        full_path_file_name = get_full_path_file_name(folder_name, file_name)
        root = None
        ns_map = []
        namespace_dictionary = {}
        events = "start", "start-ns", "end"
        # iterparse is my only option for capturing namespaces, and iterparse only reads files not strings
        try:
            for event, elem in iterparse(full_path_file_name, events):
                if event == "start-ns":
                    namespace_dictionary[elem[0]] = elem[1]
                    ns_map.append(elem)
                elif event == "start":
                    if root is None:
                        root = elem
                    for prefix, uri in ns_map:
                        elem.set("xmlns:" + prefix, uri)
                    ns_map = []
            self._register_global_namespaces(namespace_dictionary)
        except FileNotFoundError:
            print('Unable to read xml file from ' + full_path_file_name)
        return ElementTree(root), namespace_dictionary

    def _register_global_namespaces(self, namespace_dictionary):
        """ Register namespaces to allow output to include readable namespace aliases """
        for prefix in namespace_dictionary:
            uri = namespace_dictionary[prefix]
            register_namespace(prefix, uri)

    def _get_metadata_given_url(self, url):
        """ Return xml from URL."""
        xml_as_string = ""
        try:
            xml_as_string = request.urlopen(url).read().decode('utf-8')
        except error.HTTPError:
            print('Unable to retrieve xml from ' + url)
            pass
        except ConnectionRefusedError:
            print('Connection refused on url ' + url)
        except:  # noqa E722 - intentionally ignore warning about bare except
            print('Error caught trying to process url ' + url)
        return xml_as_string

    def _get_snite_metadata_url(self, embark_server_address, mode):
        """ Get url for retrieving Snite metadata """
        base_url = embark_server_address \
            + "/results.html?layout=marble_mets&format=xml&maximumrecords=-1&recordType=objects_1"
        if mode == 'full':
            url = base_url + "&query=_ID=ALL"
        else:  # incremental
            recent_past = datetime.utcnow() - timedelta(days=2)
            recent_past_string = recent_past.strftime('%m/%d/%Y')
            url = base_url + "&query=mod_date%3E%22" + recent_past_string + "%22"
        return(url)

    def _test_for_missing_fields(self, object_id, xml, namespace_dictionary, required_fields):
        """ Test for missing required fields """
        missing_fields = ''
        for preferred_name, xpath in required_fields.items():
            value = self._get_value_given_xpath(xml, xpath, namespace_dictionary)
            if value == '' or value is None:
                missing_fields += preferred_name + ' - at xpath location ' + xpath + '\n'
        if missing_fields > '':
            self._log_missing_field(object_id, missing_fields)
            return(object_id + ' is missing the follwing required field(s): \n' + missing_fields + '\n')
        return(missing_fields)

    def _log_missing_field(self, object_id, missing_fields):
        """ Log missing field information """
        with push_scope() as scope:
            scope.set_tag('repository', 'snite')
            scope.set_tag('problem', 'missing_field')
            scope.level = 'warning'
            capture_message(object_id + ' is missing the follwing required field(s): \n' + missing_fields)

    def _get_value_given_xpath(self, xml, xpath, namespace_dictionary):
        """ Return the first non-empty value given an xpath """
        value = ''
        for item in xml.findall(xpath, namespace_dictionary):
            value = item.text
            if value is None and '[@' in xpath:  # See if we need to look for an attribute
                attribute_name = re.search(r'(?<=@)\w+', xpath)[0]  # Get the first word after "@"
                value = item.get(attribute_name)
            if value is not None:
                break  # we only care about the first one that is populated
        return value

    def notify(self, missing_fields):
        recipients = self.config['notification-email-address'].split(",")
        sender = self.config['no-reply-email-address']
        subject = "Metadata is missing required fields"
        body_text = "Missing required fields when processing metadata.  " + missing_fields
        body_html = """<html>
        <head></head>
        <body>
        <h1>Missing required fields when processing metadata</h1>
        <p> """ + missing_fields + """</p>
        </body>
        </html>"""
        body_html = body_html.replace('\n', '<br/>')
        body_text = ''
        self._send_email(sender, recipients, subject, body_html, body_text)
        return

    def _send_email(self, SENDER, recipients, subject, body_html, body_text):
        AWS_REGION = "us-east-1"
        CHARSET = "UTF-8"
        client = boto3.client('ses', region_name=AWS_REGION)
        email_message_json = {
            'Body': {},
            'Subject': {
                'Charset': CHARSET,
                'Data': subject,
            },
        }
        if body_html > '':
            email_message_json['Body']['Html'] = {'Charset': CHARSET, 'Data': body_html}
        if body_text > '':
            email_message_json['Body']['Text'] = {'Charset': CHARSET, 'Data': body_text}
        try:
            response = client.send_email(
                Destination={'ToAddresses': recipients},
                Message=email_message_json,
                Source=SENDER
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            print("Email sent! Message ID:"),
            print(response['MessageId'])
        return
