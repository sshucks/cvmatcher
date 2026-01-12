import pandas as pd
from fastapi import FastAPI, UploadFile, Form, File, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os, json
import tempfile, shutil

from typing import List, Optional
from config import CV_OUTPUT_DIR, APPLICATION_SETTINGS_PATH, MATCHING_HISTORY_PATH
from caching.utils import save_input_cvs, get_all_cvs
from pipeline import pipeline_llm_parsing_previous_matching as pipeline
from config import DEFAULT_MATCHING_CONFIG
from pprint import pp

from caching.utils import hash_in_database, get_cv_info
from utils.utils import update_history, load_application_settings

app = FastAPI()

# def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants):
#     results, warnings = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n, applicants)
#     return results, warnings
#
#
# def extract_cv(file_path, hash):
#     # make API call to extract information and store response JSON
#     output_file = os.path.join(CV_OUTPUT_DIR, f"{os.path.splitext(hash)[0]}.json")
#     process_cv_php(file_path, output_file)
#
#     read_json_file(output_file)

@app.get("/settings")
async def get_settings():
    """Get the current settings of the application
    :return: JSONResponse containing the settings
    """
    print("GET /settings called")
    try:
        print(f"Fetching settings from {APPLICATION_SETTINGS_PATH}")
        with open(APPLICATION_SETTINGS_PATH, "r") as f:
            print("Settings file opened successfully")
            settings = json.load(f)
        return JSONResponse(content=settings, status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
        
@app.post("/settings")
async def update_settings(new_settings: dict):
    """Update the settings of the application
    :param new_settings: dictionary containing the new settings
    :return: JSONResponse indicating success or failure
    """
    print("POST /settings called")
    try:
        print(f"Updating settings at {APPLICATION_SETTINGS_PATH} with: {new_settings}")
        with open(APPLICATION_SETTINGS_PATH, "r") as f:
            print("Settings file opened successfully")
            settings = json.load(f)
        
        for key, value in new_settings.items():
            settings[key] = value
            
        with open(APPLICATION_SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
            print("Settings file updated successfully")
        return JSONResponse(
            content={"message": "Settings updated successfully."},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
@app.get("/history")
async def get_history():
    """Get the history of processed CVs
    :return: JSONResponse containing the history
    """
    print("GET /history called")
    try:
        print(f"Fetching history from {MATCHING_HISTORY_PATH}")
        print(f"History file exists: {os.path.exists(MATCHING_HISTORY_PATH)}")
        with open(MATCHING_HISTORY_PATH, "r") as f:
            history = json.load(f)
        print("History fetched successfully")
        print(f"History content: {history}")
        return JSONResponse(content=history, status_code=status.HTTP_200_OK)       
    except Exception as e:
        print("Error fetching history:", repr(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )
@app.delete("/history")
async def clear_history():
    """Clear the history of processed CVs
    :return: JSONResponse indicating success or failure
    """
    print("DELETE /history called")
    try:
        print(f"Clearing history at {MATCHING_HISTORY_PATH}")
        with open(MATCHING_HISTORY_PATH, "w") as f:
            json.dump([], f)  # reset history to empty list
            print("History cleared successfully")
        return JSONResponse(
            content={"message": "History cleared successfully."},
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )

@app.get("/get_cv/{cv_hash}")
async def get_cv(cv_hash:str, download: bool = False):
    """Get a parsed CV file based on its hash
    :param cv_request: request containing the hash of the CV and whether to download the file
    :return: File response containing the parsed CV or JSONResponse containing error message
    """
    print("GET /get_cv called")
    try:
        print(f"Received request for CV with hash: {cv_hash}, download={download}")
        if hash_in_database(cv_hash):
            print(f"CV with hash {cv_hash} found in database.")
            
            cv_info = get_cv_info(cv_hash)
            print(f"Retrieved CV info from database: {cv_info}")
            cv_path = cv_info.path if cv_info else None
            filename = cv_info.file_name if cv_info else None
            
            if cv_path is None:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": f"CV with hash {cv_hash} not found in database."}
                )
            else:
                print(f"CV file path retrieved: {cv_path}")
            
            disposition_type = "attachment" if download else "inline"
            
            file_response =  FileResponse(
                path=cv_path, 
                media_type='application/pdf', 
                filename=filename,
                content_disposition_type=disposition_type
            )
            
            
            return file_response
           
            
        else:
            print(f"CV with hash {cv_hash} not found in database.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"CV with hash {cv_hash} not found in database."}
            )
        
    except Exception as e:
        # print(repr(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)}
        )

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
        files_for_matching = None
        # compute provided CVs if present
        if input_cvs:
            # store CVs in filesystem, calculate hash and insert into database
            files_for_matching = await save_input_cvs(input_cvs)
            #print(files_for_matching)
        else:
            print("No input cvs received")

        
        # determine the applicants to score
        applicants = {}
        if all_cvs:
            # if the flag for all cvs is checked, use all CVs in database
            applicants["parsed"] = await get_all_cvs() # get all parsed CVs in the database
              
            if files_for_matching:
                hashes_parsed = [os.path.basename(f[0]).split(".")[0] for f in applicants["parsed"]] # get the hashes for all parsed CVs
                applicants["raw"] = [file for file in files_for_matching if os.path.basename(file[0]).split(".")[0] not in hashes_parsed] # mark uploaded CVs for parsing based on if they are not already parsed

            
        elif input_cvs:
            # if cvs are provided, use only provided CVs
            applicants["parsed"] = [file for file in files_for_matching if os.path.basename(file[0]).split(".")[-1] == "json"] # filter the already parsed CVs from the list of paths

            # get the CVs to parse from the list of paths
            hashes_parsed = [ os.path.basename(f).split(".")[0] for f in os.listdir(CV_OUTPUT_DIR)]
            applicants["raw"] = [file for file in files_for_matching if os.path.basename(file[0]).split(".")[0] not in hashes_parsed]

        # if no CVs are provided and the all CVs flag is not checked, return errors
        if not all_cvs and not input_cvs:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "results": None,
                    "error": "Neither a list of CVs was provided nor the option to use all CVs in the database was checked. Please provide some CVs or check the option to use all CVs in the database."
                }
            )

        # define the weights used for matching based on the user input
        weighted_config = DEFAULT_MATCHING_CONFIG.copy()
        weighted_config["education"]["weight"] = edu_weight
        weighted_config["professional_experience"]["weight"] = exp_weight
        weighted_config["hard_skills"]["weight"] = pro_weight
        weighted_config["soft_skills"]["weight"] = per_weight

        # generate a temporary file of the requirements file so it can be read/processed in the pipeline
        suffix = os.path.splitext(requirements.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(requirements.file, tmp)
            tmp_path = tmp.name
            
        # Call the pipeline for parsing and matching
        results_df, warnings = pipeline.run_multiple_cvs(requirement_path= tmp_path, 
                                                         cv_paths=applicants, 
                                                         args=weighted_config )
        
        results_df['applicant_hash'] = results_df['cv_path'].apply(lambda x: os.path.basename(x).split('.')[0])
        
        results_df = results_df.sort_values(by="Score", ascending=False).head(n)
        
        results_df.drop(columns=["cv_path"], inplace=True)
             
        if results_df is None:
            return JSONResponse(content={"error": "Error while extracting requirements! Check structure of requirements file and try again.", "warnings": warnings}, status_code=500)

        app_settings = load_application_settings()
        decision_threshold = app_settings.get("Threshold", {}).get('value', 50)
        
        update_history(requirements_file=requirements.filename, 
                       cout_cvs=len(results_df), 
                       accepted=len(results_df[results_df['Score'] >= decision_threshold]), 
                       rejected=len(results_df[results_df['Score'] < decision_threshold]))
        
        response = JSONResponse(content={
            "results": results_df.to_dict(orient="records"),
            "warnings": warnings or None  # Return None if empty
        })

        return response
    except Exception as e:
        print(repr(e))
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        # delete the temporary requirements file that was created
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)