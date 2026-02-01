import json
from fastapi import FastAPI, UploadFile, Form, File, status
from typing import List, Optional
import requests
import hashlib
import io

app = FastAPI()

@app.post("/cv-parsing")
def parse_cv_endpoint(cv_files:Optional[List[UploadFile]] = File(None), db_cvs: bool = Form(False)) -> List[dict]:
    print("In CV-Parsing")
    # read cv json file alternatively process cv file using llm
    cv_data = []
    hashes = set()

    if db_cvs:
        response = requests.get("http://data-access-service:8000/get-all-jsons")

        if response.status_code != 200:
            print("CVs from database could not be extracted")

        cv_data = response.json()
        hashes = {item["file_hash"] for item in cv_data}

    
    # iterate over uploaded files
    for file in cv_files:
        #content = file.file.read().decode("utf-8")

        print("Process CV")

        # Calculate SHA256 hash
        hash_digest = hashlib.file_digest(file.file, "sha256").hexdigest()

        if hash_digest not in hashes:
            # only process if not already in cv_data

            if not db_cvs:
                # dont use all cvs, but look for already processed cvs
                response = requests.get(
                    "http://data-access-service:8000/get-cv-json",
                    params={"hash": hash_digest}  # pass query parameters correctly
                )

                if response.status_code == 200:
                    cv_json = response.json()
                    cv_json["file_hash"] = hash_digest
                    cv_data.append(cv_json)

                else:
                    """cv_json = # process JSON
                    cv_json["file_hash"] = hash_hex
            
                    cv_data.append(cv_json)"""

                    file.file.seek(0)  # ensure pointer is at start
                    file_bytes = file.file.read()  # read bytes

                    # wrap in BytesIO for requests
                    file_io = io.BytesIO(file_bytes)

                    response = requests.post(
                        "http://data-access-service:8000/upload-pdf",
                        files={"file": ("myfile.pdf", file_io, "application/pdf")}
                    )

            
        file.file.close()
    
    return cv_data