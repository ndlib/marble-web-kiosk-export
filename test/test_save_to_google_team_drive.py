# test_create_new_index_record.py
""" test create_new_index_record """
import os
import sys
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies")
import unittest  # noqa: E402
from src.save_to_google_team_drive import save_file_to_google_team_drive, \
    _get_file_id_given_filename, \
    _delete_existing_file, \
    _update_existing_file, \
    _upload_new_file, \
    _get_credentials_from_service_account_info  # noqa: E402
from src.get_config import get_config  # noqa: E402
import time  # noqa: E402


class Test(unittest.TestCase):
    """ Class for test fixtures """
    # def __init__(self):
    # credentials = _get_credentials_from_service_account_file()
    config = get_config()
    google_credentials = config['google']['credentials']
    credentials = _get_credentials_from_service_account_info(google_credentials)
    snite_metadata_team_drive_id = config['google']['metadata']['drive-id']  # '0AASeuQIa42uxUk9PVA'
    snite_metadata_folder_id = config['google']['metadata']['parent-folder-id']  # '1F5cgW7ORRGHcpy2fbYiFE528RuDjHnrJ'
    local_folder_name = 'test'
    file_name = 'test.xml'

    # Note:  Tests are run alphabetically!  I added numbers in the names to force running sequentially
    def test_1_get_credentials_from_service_account_info(self):
        """ Test returning credentials from service account info """
        print('1 - test_get_credentials_from_service_account_info')
        self.assertTrue(self.credentials)

    def test_2_save_file_to_google_team_drive(self):
        """ Test saving a file to google team drive. """
        print('2 - test_save_file_to_google_team_drive')
        file_id = save_file_to_google_team_drive(self.google_credentials,
                                                 self.snite_metadata_team_drive_id,
                                                 self.snite_metadata_folder_id,
                                                 self.local_folder_name,
                                                 self.file_name)
        self.assertTrue(file_id > "")

    def test_3_known_file_exists(self):
        print('3 - test_known_file_exists')
        time.sleep(5)  # wait so asynchronous above save completes
        file_id = _get_file_id_given_filename(self.credentials,
                                              self.snite_metadata_team_drive_id,
                                              self.snite_metadata_folder_id,
                                              self.file_name)
        self.assertTrue(file_id > "")

    def test_4_update_existing_file(self):
        print('4 - test_update_existing_file')
        file_id = _get_file_id_given_filename(self.credentials,
                                              self.snite_metadata_team_drive_id,
                                              self.snite_metadata_folder_id,
                                              self.file_name)
        updated_file_id = _update_existing_file(self.credentials,
                                                self.snite_metadata_folder_id,
                                                file_id,
                                                self.local_folder_name,
                                                self.file_name)
        self.assertTrue(file_id == updated_file_id)

    def test_5_delete_file(self):
        print('5 - test_delete_file')
        file_id = _get_file_id_given_filename(self.credentials,
                                              self.snite_metadata_team_drive_id,
                                              self.snite_metadata_folder_id,
                                              self.file_name)
        _delete_existing_file(self.credentials, file_id)
        time.sleep(5)  # wait so asynchronous delete completes
        file_id = _get_file_id_given_filename(self.credentials,
                                              self.snite_metadata_team_drive_id,
                                              self.snite_metadata_folder_id,
                                              self.file_name)
        self.assertTrue(file_id == "")

    def test_6_upload_new_file(self):
        print('6 - test_upload_new_file')
        file_id = _upload_new_file(self.credentials,
                                   self.snite_metadata_team_drive_id,
                                   self.snite_metadata_folder_id,
                                   self.local_folder_name,
                                   self.file_name)
        self.assertTrue(file_id > "")
        _delete_existing_file(self.credentials, file_id)  # clean up after ourselves


def suite():
    """ define test suite """
    return unittest.TestLoader().loadTestsFromTestCase(Test)


if __name__ == '__main__':
    suite()
    unittest.main()
