# xml_manipulation.py
""" This routine reads includes xml-related tasks. """

import re
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from file_system_utilities import create_directory, get_full_path_file_name  # noqa: E402


def get_value_given_xpath(xml, xpath, namespace_dictionary):
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


def write_xml_output_file(folder_name, file_name, xml_tree):
    """ Write xml to output file """
    create_directory(folder_name)
    full_path_file_name = get_full_path_file_name(folder_name, file_name)
    xml_tree.write(full_path_file_name, encoding="utf-8", xml_declaration=True)


def save_string_of_xml_to_disk(folder_name, file_name, xml_as_string):
    """ Write string of xml to disk """
    create_directory(folder_name)
    full_path_file_name = get_full_path_file_name(folder_name, file_name)
    with open(full_path_file_name, "w") as xml_file:
        xml_file.write(xml_as_string)
