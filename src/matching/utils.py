from datetime import date

def parse_custom_date(date_string: str) -> str | None:
    """Parse a date and return a string representation.

    :param date_string: parse a date in the format |YYYY|MM|DD|--|--|
    :type date_string: str
    :return: return a date string in format DD.MM.YYYY or None if an error occured
    :rtype: str | None
    """
    
    try:
        # split provided date at '|'
        parts = date_string.split('|')

        # check if at least 3 parts are present
        if len(parts) < 3:
            return None

        # convert date parts to numbers
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        # parse date and return formated string
        parsed_date_object = date(year, month, day)
        return parsed_date_object.strftime("%d.%m.%Y")
    
    except (ValueError, IndexError):
        # handle missing parts ore conversion errors
        return None

from fastapi import UploadFile
import hashlib

def generate_file_hash(file: UploadFile) -> str:
    """Calculate the hash value of a file

    :param file: file for hash value calculation
    :type file: UploadFile
    :return: hex representation of hash code
    :rtype: str
    """
    # calculate hashcode
    digest = hashlib.file_digest(file, "sha256")

    # reset pointer to beginning of file, for further consumption
    file.seek(0)

    # return hex representation of hash
    return digest.hexdigest()