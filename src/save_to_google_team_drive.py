# save_to_google_team_drive.py
""" Saves a file to a Google Team Drive, in a given parent folder """

import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from google.oauth2 import service_account  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402


def _get_credentials_from_service_account_info(google_credentials):
    """ Return credentials given service account file and assumptions of scopes needed """
    service_account_info = google_credentials
    credentials = ""
    # Scopes are defined here:  https://developers.google.com/identity/protocols/googlescopes
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return(credentials)


def save_file_to_google_team_drive(google_credentials, drive_id, parent_folder_id, local_folder_name, file_name):
    """ If file exists, update it, else do initial upload """
    # credentials = _get_credentials_from_service_account_file()
    credentials = _get_credentials_from_service_account_info(google_credentials)
    file_id = _get_file_id_given_filename(credentials, drive_id, parent_folder_id, file_name)
    if file_id > "":
        _update_existing_file(credentials, parent_folder_id, file_id, local_folder_name, file_name)
    else:
        file_id = _upload_new_file(credentials, drive_id, parent_folder_id, local_folder_name, file_name)
    return(file_id)


def _get_file_id_given_filename(credentials, drive_id, parent_folder_id, file_name):
    """ Find a File_Id given drive, parent folder, and file_name """
    file_id = ""
    service = build('drive', 'v3', credentials=credentials)
    nextPageToken = ""
    query_string = "name='" + file_name + "'" + " and '" + parent_folder_id + "' in parents"
    query_string += " and trashed = False"
    results = service.files().list(
        pageSize=1000,  # 1000 is the maximum pageSize allowed
        pageToken=nextPageToken,
        fields="kind, nextPageToken, incompleteSearch, files(id, name, mimeType, modifiedTime, parents)",
        supportsAllDrives="true",  # required if writing to a team drive
        driveId=drive_id,
        includeItemsFromAllDrives="true",  # required if querying from a team drive
        corpora="drive",
        q=query_string).execute()
    items = results.get('files', [])
    if items:
        for item in items:
            if 'id' in item:
                file_id = item['id']
            break  # if more than one file exists, we'll just return the first one
    return file_id


def _update_existing_file(credentials, parent_folder_id, file_id, local_folder_name, file_name, mime_type='text/xml'):
    """ upload new content for existing file_id """
    full_path_file_name = _get_full_path_file_name(local_folder_name, file_name)
    media = MediaFileUpload(full_path_file_name,
                            mimetype=mime_type,
                            resumable=True)  # 'image/jpeg'
    drive_service = build('drive', 'v3', credentials=credentials)
    file = drive_service.files().update(fileId=file_id,
                                        media_body=media,
                                        supportsAllDrives=True,
                                        fields='id').execute()
    return(file.get('id'))


def _upload_new_file(credentials, drive_id, parent_folder_id, local_folder_name, file_name, mime_type='text/xml'):
    """ Upload an all new file (note, this will produce duplicates,
        so check for existance before calling this) """
    full_path_file_name = _get_full_path_file_name(local_folder_name, file_name)
    file_metadata = {'name': file_name, 'mimeType': mime_type,
                     'teamDriveId': drive_id,
                     'parents': [parent_folder_id]}
    media = MediaFileUpload(full_path_file_name,
                            mimetype=mime_type,
                            resumable=True)  # 'image/jpeg'
    drive_service = build('drive', 'v3', credentials=credentials)
    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        supportsAllDrives=True,
                                        fields='id').execute()
    return(file.get('id'))


def _get_full_path_file_name(local_folder_name, file_name):
    full_path_file_name = ''
    if local_folder_name > '':
        full_path_file_name = local_folder_name + '/'
    full_path_file_name += file_name
    return full_path_file_name


def _delete_existing_file(credentials, file_id):
    """ Delete an existing file given file_id """
    # note: user needs "organizer" privilege on the parent folder in order to delete
    drive_service = build('drive', 'v3', credentials=credentials)
    drive_service.files().delete(fileId=file_id,
                                 supportsAllDrives=True).execute()
