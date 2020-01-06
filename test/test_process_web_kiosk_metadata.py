# test_create_new_index_record.py
""" test create_new_index_record """
import os
import sys
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies")
import unittest  # noqa: E402
from src.process_web_kiosk_metadata import processWebKioskMetsMetadata  # noqa: E402
from src.get_config import get_config  # noqa: E402
from src.file_system_utilities import delete_file  # noqa: E402
# from xml.etree.ElementTree import ElementTree, tostring


class Test(unittest.TestCase):
    """ Class for test fixtures """
    config = get_config()
    # with open("config.json", 'r') as input_source:
    #     data = json.load(input_source)
    # input_source.close()
    # config = data["config"]
    config['runningUnitTests'] = True
    folder_name = config['folderName']
    file_name = config['fileName']
    drive_id = config['google']['museum']['metadata']['drive-id']
    parent_folder_id = config['google']['museum']['metadata']['parent-folder-id']
    required_fields = config['xmlRequiredFields']
    clean_up_as_we_go = False

    web_kiosk_class = processWebKioskMetsMetadata(config)

    # Note:  Tests are run alphabetically!  I added numbers in the names to force sorting
    def test_1_get_snite_composite_mets_metadata(self):
        """ Test retrieving Snite composite METS metadata """
        print('1 - test_1_get_snite_composite_mets_metadata')
        xml_as_string = self.web_kiosk_class.get_snite_composite_mets_metadata()
        self.assertTrue(xml_as_string > '')

    def test_2_process_snite_composite_mets_metadata(self):
        """ Test processing Snite composite METS metadata. """
        print('2 - test_process_snite_composite_mets_metadata')
        namespace_dictionary = self.web_kiosk_class.process_snite_composite_mets_metadata(self.clean_up_as_we_go)
        self.assertFalse(namespace_dictionary == {})

    def test_3_process_incremental_with_cleanup(self):
        """ Test processing incremental Snite composite METS metadata with cleanup. """
        print('3 - test_process_snite_composite_mets_metadata')
        self.config['mode'] = 'incremental'
        self.clean_up_as_we_go = True
        self.web_kiosk_class.__init__(self.config)
        xml_as_string = self.web_kiosk_class.get_snite_composite_mets_metadata()
        if xml_as_string > '':
            namespace_dictionary = self.web_kiosk_class.process_snite_composite_mets_metadata(self.clean_up_as_we_go)
        self.assertFalse(namespace_dictionary == {})

    def test_4_clean_up_after_ourselves(self):
        """ Clean up after ourselves """
        print('4 - clean up after ourselves')
        delete_file(self.folder_name, self.file_name)
        self.assertTrue(True)


def suite():
    """ define test suite """
    return unittest.TestLoader().loadTestsFromTestCase(Test)


if __name__ == '__main__':
    suite()
    unittest.main()
