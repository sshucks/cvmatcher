from fastapi import FastAPI, UploadFile, Form, File, status
from typing import List
from fastapi.responses import JSONResponse
import sys
import os
from typing import List

from src.config import CV_INPUT_DIR, CV_OUTPUT_DIR, CV_OUTPUT_DIR_MATCHING
from src.caching import get_db
from src.caching.models import CachedCVs
from src.caching.CachedCV_Wrapper import CachedCV_Wrapper

from tqdm import tqdm



from typing import List, Optional


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_applicants import match_applicant
from extracting.cv.process_cvs import convert_docx_to_pdf, process_cv_php
from extracting.read_json import read_json_file, save_json
from matching.utils import generate_file_hash

app = FastAPI()

def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants):
    results, warnings = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n, applicants)
    return results, warnings

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
    """Store and extract provided CVs, if they don't already exist (check via file hash)

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
            cv = CachedCV_Wrapper(hash_digest, file_path, True)
            print(f"{hash_digest} already exists, SKIPPING")
        else:
            await store_cv(hash=hash_digest, file_name=file_name, output_dir=CV_INPUT_DIR, file=cv)
            
            if "docx" in file_path:
                file_path = file_path.replace("docx","pdf")

            extract_cv(file_path, hash_digest)

            # write extracted CV to database
            with get_db() as db:
                cv_entry = CachedCVs(cv_hash=hash_digest, path=file_path, file_name=cv.filename)
                db.add(cv_entry)
                db.commit()
            
        results.append(hash_digest)
    
    # return hash values for further usage
    return results


def extract_cv(file_path, hash):
    # make API call to extract information and store response JSON
    output_file = os.path.join(CV_OUTPUT_DIR, f"{os.path.splitext(hash)[0]}.json")
    process_cv_php(file_path, output_file)
        
    read_json_file(output_file)


@app.post("/process")
async def process_matching(
    requirements: UploadFile = File(...),
    input_cvs: Optional[List[UploadFile]] = File(None),
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
        # compute provided CVs if present
        if input_cvs:
            # store and extract CVs in filesystem and calculate hash and insert into database
            files_for_matching = await save_input_cvs(input_cvs)            
        else:
            print("No input cvs received")
        
        # determine the applicants to score
        applicants = None
        if all_cvs:
             # if the flag for all cvs is checked, use all CVs in database
            applicants = os.listdir(CV_OUTPUT_DIR_MATCHING)
            # remove non-json files
            applicants = [file.removesuffix(".json") for file in applicants if file.endswith('.json')]
        elif input_cvs: 
            # if cvs are provided, use only provided CVs
            applicants = files_for_matching
        
        # if no CVs are provided and the all CVs flag is not checked, return errors
        if not all_cvs and not input_cvs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "results": None,
                    "error": "Neither a list of CVs was provided nor the option to use all CVs in the database was checked. Please provide some CVs or check the option to use all CVs in the database."
                }
            )
        # Call the matching logic
        results_df, warnings = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants)

        if results_df is None:
            return JSONResponse(content={"error": "Error while extracting requirements! Check structure of requirements file and try again.", "warnings": warnings}, status_code=500)

        response = JSONResponse(content={
            "results": results_df.to_dict(orient="records"),
            "warnings": warnings or None  # Return None if empty
        })

        return response
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
