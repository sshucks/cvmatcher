from fastapi import FastAPI, UploadFile, Form, File
from typing import List
from fastapi.responses import JSONResponse
import pandas as pd
import sys
import os
from typing import List
import hashlib

from src.config import CV_DATABASE


from typing import List


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_applicants import match_applicant

app = FastAPI()

def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n):
    results = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n)
    print(results)
    return results

def save_input_cvs(input_cvs:List[UploadFile]) -> list:
    """Store all provided CVs

    :param input_cvs: List of CVs to store
    :type input_cvs: List[UploadFile]
    
    :return: list of hash values for further usage
    :rtype: list of str 
    """
    
    hash_values = []
    
    # for every file
    for cv in input_cvs:
        
        # generate hash value
        hash_digest = generate_file_hash(cv.file)
        hash_values.append(hash_digest)
        
        # generate new file name
        suffix = str(cv.filename).split('.')[-1]
        file_name =f"{hash_digest}.{suffix}"
        
        # store input file in file system    
        file_path = os.path.join(CV_DATABASE, file_name)
        with open(file_path, "wb") as f:
            f.write(cv.file.read())
    
    # return hash values for further usage
    return hash_values

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


@app.post("/process")
async def process_matching(
    requirements: UploadFile = File(...),
    input_cvs: List[UploadFile] = File(...),
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
        # TODO: store CVs in filesystem and calculate hash and insert into database
        file_hashes = save_input_cvs(input_cvs)
        
        # TODO: extract CVs using API

        # Call the matching logic
        results_df = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n)
        
        # Return the results as JSON
        return JSONResponse(content={"results": results_df.to_dict(orient="records")})
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
