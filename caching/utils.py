import hashlib

from fastapi import FastAPI, UploadFile, Form, File, status
from typing import List
from fastapi.responses import JSONResponse
import sys
import os
from typing import List

from config import CV_INPUT_DIR, CV_OUTPUT_DIR, CV_OUTPUT_DIR_MATCHING
from caching import get_db
from caching.models import CachedCVs
from caching.CachedCV_Wrapper import CachedCV_Wrapper
from tqdm import tqdm
from typing import List, Optional

from utils.utils import convert_docx_to_pdf

def hash_in_database(hash:str) -> bool:
    """Check in database if CV hash already exists

    :param hash: hash of CV file
    :type hash: str
    :return: whether the CV file behind the hash is already stored
    :rtype: bool
    """
    with get_db() as db:
        # get first result of equal hash value
        result = db.query(CachedCVs).filter(CachedCVs.cv_hash==str(hash)).first()
        
        # return if result exists
        return True if result else False
    
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

async def store_cv(hash:str, file_name:str, output_dir:str, file:UploadFile):
    """Store the provided file in the filesystem. If it is DOCX, convert to PDF first.

    :param hash: hash value of file
    :type hash: str
    :param file_name: file_name of the provided file
    :type file_name: str
    :param output_dir: location (directory) where to store the file
    :type output_dir: str
    :param file: document to store
    :type file: UploadFile
    """
    # check file type
    file_suffix = file_name.split(".")[-1].lower() 
    file_path = os.path.join(output_dir, file_name)

    # create directory if not existing
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    match file_suffix:
        case "pdf":
            with open(file_path, "wb") as f:
                f.write(file.file.read())
        
        case "docx":
            await convert_docx_to_pdf(file=file, new_name=hash, output_dir=CV_INPUT_DIR)
        
        case _:
            pass


async def save_input_cvs(input_cvs:List[UploadFile]) -> list:
    """Store provided CVs, if they don't already exist (check via file hash)

    :param input_cvs: List of CVs to store
    :type input_cvs: List[UploadFile]
    
    :return: list of hash values for further usage
    :rtype: list of str
    """
    
    results = []
    
    # for every file
    for cv in input_cvs:
        
        # generate hash value
        hash_digest = generate_file_hash(cv.file)
        
        # check if hash already exists
        file_exists = hash_in_database(hash_digest)
        
        # generate new file name
        suffix = str(cv.filename).split('.')[-1]
        file_name =f"{hash_digest}.{suffix}"
            
        # put together path for file location
        file_path = os.path.join(CV_INPUT_DIR, file_name)
        
        if file_exists:
            # TODO: implement logging
             # add file to results
            #cv = CachedCV_Wrapper(hash_digest, file_path, True)
            print(f"{hash_digest} already exists, SKIPPING")
            file_path = os.path.join(CV_OUTPUT_DIR, f"{hash_digest}.json")
        else:
            await store_cv(hash=hash_digest, file_name=file_name, output_dir=CV_INPUT_DIR, file=cv)
            
            if "docx" in file_path:
                file_path = file_path.replace("docx","pdf")

            # write file path (hash) of CV to database
            with get_db() as db:
                cv_entry = CachedCVs(cv_hash=hash_digest, path=file_path, file_name=cv.filename)
                db.add(cv_entry)
                db.commit()
            
        results.append(file_path)
    
    # return hash values for further usage
    return results