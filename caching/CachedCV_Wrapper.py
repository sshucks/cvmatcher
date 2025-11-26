import os
from config import CV_OUTPUT_DIR_MATCHING

class CachedCV_Wrapper:
    """Representation of a cached CV
    """
    def __init__(self, hash_digest:str, file_path:str, already_extracted:bool):
        """_summary_

        :param hash_digest: hash value of cached file
        :type hash_digest: str
        :param file_path: location in file system of cached file
        :type file_path: str
        :param already_extracted: flag whether the file has already been extracted
        :type already_extracted: bool
        """
        
        self.hash_digest = hash_digest
        self.file_path = file_path
        self.already_extracted = already_extracted
    
    def get_hash_digest(self)-> str:
        """Get the hash value of the cahced file

        :return: hash value
        :rtype: str
        """
        return self.hash_digest
    
    def get_file_path(self)-> str:
        """Get the file path

        :return: location of cached file in file system
        :rtype: str
        """
        return self.file_path
    
    def is_extracted(self)-> bool:
        """Get extraction status

        :return: whether the cached file has been extracted
        :rtype: bool
        """
        return self.already_extracted
    
    def get_extracted_path(self)->str:
        """Get the file name of the extracted information

        :return: file name of the JSON file containing the extracted information
        :rtype: str
        """
        return f"{self.hash_digest}.json"
    
    def __str__(self) -> str:
        return f"CachedCV_Wrapper[hash_digest={self.hash_digest}, file_path = {self.file_path}, is_extracted={self.already_extracted}]"