# save_to_google_team_drive.py
""" Saves a file to a Google Team Drive, in a given parent folder """

import os
import sys
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am)
sys.path.append(where_i_am + "/dependencies")
# from google.oauth2 import service_account  # noqa: E402
# from googleapiclient.discovery import build  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402


def save_file_to_google_team_drive(google_connection, drive_id, parent_folder_id, local_folder_name, file_name, mime_type='text/xml'):  # noqa E501
    """ If file exists, update it, else do initial upload """
    file_id = _get_file_id_given_filename(google_connection, drive_id, parent_folder_id, file_name)
    if file_id > "":
        _update_existing_file(google_connection, parent_folder_id, file_id, local_folder_name, file_name, mime_type)
    else:
        file_id = _upload_new_file(google_connection, drive_id, parent_folder_id, local_folder_name, file_name, mime_type)  # noqa: E501
    return(file_id)


def _get_file_id_given_filename(google_connection, drive_id, parent_folder_id, file_name):
    """ Find a File_Id given drive, parent folder, and file_name """
    file_id = ""
    nextPageToken = ""
    query_string = "name='" + file_name + "'" + " and '" + parent_folder_id + "' in parents"
    query_string += " and trashed = False"
    results = google_connection.files().list(
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


def _update_existing_file(google_connection, parent_folder_id, file_id, local_folder_name, file_name, mime_type='text/xml'):    # noqa: E501
    """ upload new content for existing file_id """
    full_path_file_name = _get_full_path_file_name(local_folder_name, file_name)
    media = MediaFileUpload(full_path_file_name,
                            mimetype=mime_type,
                            resumable=True)  # 'image/jpeg'
    file = google_connection.files().update(fileId=file_id,
                                            media_body=media,
                                            supportsAllDrives=True,
                                            fields='id').execute()
    return(file.get('id'))


def _upload_new_file(google_connection, drive_id, parent_folder_id, local_folder_name, file_name, mime_type='text/xml'):  # noqa: E501
    """ Upload an all new file (note, this will produce duplicates,
        so check for existance before calling this) """
    full_path_file_name = _get_full_path_file_name(local_folder_name, file_name)
    file_metadata = {'name': file_name, 'mimeType': mime_type,
                     'teamDriveId': drive_id,
                     'parents': [parent_folder_id]}
    media = MediaFileUpload(full_path_file_name,
                            mimetype=mime_type,
                            resumable=True)  # 'image/jpeg'
    file = google_connection.files().create(body=file_metadata,
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


def _delete_existing_file(google_connection, file_id):
    """ Delete an existing file given file_id """
    # note: user needs "organizer" privilege on the parent folder in order to delete
    google_connection.files().delete(fileId=file_id,
                                     supportsAllDrives=True).execute()
