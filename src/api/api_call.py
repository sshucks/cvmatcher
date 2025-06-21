from fastapi import FastAPI, UploadFile, Form, File
from typing import List
from fastapi.responses import JSONResponse
import pandas as pd
import sys
import os
from typing import List

from src.config import CV_INPUT_DIR, CV_OUTPUT_DIR, CV_OUTPUT_DIR_MATCHING
from caching import get_db
from caching.models import CachedCVs
from src.caching.CachedCV_Wrapper import CachedCV_Wrapper

from tqdm import tqdm



from typing import List


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_applicants import match_applicant
from extracting.cv.process_cvs import convert_docx_to_pdf, process_cv_php
from extracting.read_json import read_json_file, save_json
from matching.utils import generate_file_hash

app = FastAPI()

def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants):
    results = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n, applicants)
    print(results)
    return results

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
    
    match file_suffix:
        case "pdf":
            with open(file_path, "wb") as f:
                f.write(file.file.read())
        
        case "docx":
            await convert_docx_to_pdf(file=file, new_name=hash, output_dir=CV_INPUT_DIR)
        
        case _:
            pass
        
        


async def save_input_cvs(input_cvs:List[UploadFile]) -> list:
    """Store provided CVs, if they don't already exists (check via file hash)

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
            results.append(CachedCV_Wrapper(hash_digest, file_path, True))
            print(f"{hash_digest} already exsits, SKIPPING")
        else:
            # store the cv in the filesystem
            await store_cv(hash=hash_digest, file_name=file_name, output_dir=CV_INPUT_DIR, file=cv)
            
            # write cached CV to database
            with get_db() as db:
                cv_entry = CachedCVs(cv_hash=hash_digest, path=file_path, file_name=cv.filename)
                db.add(cv_entry)
                db.commit()
            
            if "docx" in file_path:
                file_path = file_path.replace("docx","pdf")
                
            results.append(CachedCV_Wrapper(hash_digest, file_path, False))
    
    # return hash values for further usage
    return results


def extract_cvs(cvs:list):
    """Extract structured information from the documents using external API. Automatically skip already extracted documents.

    :param cvs: list of documents to extract
    :type cvs: list
    """
    
    # filter for files that are not extracted
    to_extract = [cv for cv in cvs if not cv.is_extracted()]
    
    # extract structured information from files
    for cv in tqdm(to_extract):
        
        # make API call to extract information and store response JSON
        output_file = os.path.join(CV_OUTPUT_DIR, f"{os.path.splitext(cv.get_hash_digest())[0]}_processed.json")
        process_cv_php(cv.get_file_path(), output_file)
        
        # read response JSON from file, process it and store it in final destination
        cv = read_json_file(output_file)
        save_json(os.path.join(CV_OUTPUT_DIR_MATCHING, os.path.basename(output_file)), cv)
        
    


@app.post("/process")
async def process_matching(
    requirements: UploadFile = File(...),
    input_cvs: List[UploadFile] = File(...),
    all_cvs: bool = Form(...),
    edu_weight: int = Form(...),
    exp_weight: int = Form(...),
    pro_weight: int = Form(...),
    per_weight: int = Form(...),
    n: int = Form(...)
):
    """Accept a file containing a requirements description and optinaly some CVs and performing applicant matching


    :param requirements: File containting the requirements for the position
    :type requirements: UploadFile
    :param input_cvs: List of CVs that are used in the scoring, if empty, whole database will be used
    :type input_cvs: List[UploadFile]
    :param all_cvs: whether to use all CVs in the database or only the provided input cvs
    :type all_cvs: bool
    :param edu_weight: weight of education
    :type edu_weight: int
    :param exp_weight: weight of working experience
    :type exp_weight: int
    :param pro_weight: weight of professional skills
    :type pro_weight: int
    :param per_weight: weight of personal skills
    :type per_weight: int
    :param n: number of top applicants to return
    :type n: int
    :return: list of top n applicants including score, age, email and birthdate
    :rtype: JSON
    """
    try:
        # store CVs in filesystem and calculate hash and insert into database
        files_for_matching = await save_input_cvs(input_cvs)
        print(files_for_matching)
        
        # extract CVs using API, and store json results
        extract_cvs(files_for_matching)
        
        # determine the applicants to score
        applicants = None
        if all_cvs:
            # use all CVs in database
            applicants = os.listdir(CV_OUTPUT_DIR_MATCHING)
        else: 
            # use only provided CVs
            applicants = [applicant.get_extracted_path() for applicant in files_for_matching]

        # call the matching logic
        results_df = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants)
        
        # return the results as JSON
        return JSONResponse(content={"results": results_df.to_dict(orient="records")})
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
