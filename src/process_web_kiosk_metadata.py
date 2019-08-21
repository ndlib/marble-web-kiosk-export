# process_web_kiosk_metadata.py
""" This routine reads a potentially huge single METS metadata output file from Web Kiosk.
    Individual xml files are created, one per object.
    These individual xml files are saved locally by object name.
    They are then uploaded to a Google Team Drive, and deleted locally. """

from urllib import request, error
from datetime import datetime, timedelta
from sentry_sdk import capture_message, push_scope, capture_exception
from xml.etree.ElementTree import ElementTree, register_namespace, iterparse
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from save_to_google_team_drive import save_file_to_google_team_drive  # noqa: E402
from file_system_utilities import delete_file, get_full_path_file_name  # noqa: E402  create_directory,
from send_notification_email import create_and_send_email_notification  # noqa: E402
from xml_manipulation import get_value_given_xpath, write_xml_output_file, save_string_of_xml_to_disk # noqa: #402


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
            save_string_of_xml_to_disk(folder_name, file_name, xml_as_string)
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
                write_xml_output_file(folder_name, local_file_name, object_xml)
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
                create_and_send_email_notification(accumulated_missing_fields,
                                                   self.config['notification-email-address'],
                                                   self.config['no-reply-email-address'])
        if clean_up_as_we_go:
            delete_file(folder_name, file_name)
        return namespace_dictionary

    def _add_xsi_to_root(self, root):
        """ Since we can't read the xsi information from the original xml file, add it here """
        root.set("xsi:schemaLocation", "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd http://purl.org/dc/terms/ \
                 http://dublincore.org/schemas/xmls/qdc/2008/02/11/dcterms.xsd \
                 http://www.vraweb.org/vracore4.htm http://www.loc.gov/standards/vracore/vra-strict.xsd")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

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
            capture_exception('Unable to read xml file from ' + full_path_file_name)
            # print('Unable to read xml file from ' + full_path_file_name)
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
            capture_exception('Unable to retrieve xml from ' + url)
            # print('Unable to retrieve xml from ' + url)
            pass
        except ConnectionRefusedError:
            capture_exception('Connection refused on url ' + url)
            # print('Connection refused on url ' + url)
        except:  # noqa E722 - intentionally ignore warning about bare except
            capture_exception('Error caught trying to process url ' + url)
            # print('Error caught trying to process url ' + url)
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
            value = get_value_given_xpath(xml, xpath, namespace_dictionary)
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
