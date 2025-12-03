import pandas as pd
from fastapi import FastAPI, UploadFile, Form, File, status
from fastapi.responses import JSONResponse
import os
import tempfile, shutil

from typing import List, Optional
from config import CV_OUTPUT_DIR
from caching.utils import save_input_cvs
from pipeline import pipeline_llm_parsing_previous_matching as pipeline
from config import DEFAULT_MATCHING_CONFIG

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
            # store CVs in filesystem, calculate hash and insert into database
            files_for_matching = await save_input_cvs(input_cvs)
            print(files_for_matching)
        else:
            print("No input cvs received")

        
        # determine the applicants to score
        applicants = {}
        if all_cvs:
             # if the flag for all cvs is checked, use all CVs in database
            applicants["parsed"] = os.listdir(CV_OUTPUT_DIR)
            hashes_parsed = [ os.path.basename(f).split(".")[0] for f in applicants["parsed"]]
            print("hashes_parsed", hashes_parsed)
            applicants["raw"] = [file for file in files_for_matching if os.path.basename(file).split(".")[0] not in hashes_parsed]
            
        elif input_cvs:
            # if cvs are provided, use only provided CVs
            applicants["parsed"] = [file for file in files_for_matching if os.path.basename(file).split(".")[-1] == "json"]
            hashes_parsed = [ os.path.basename(f).split(".")[0] for f in os.listdir(CV_OUTPUT_DIR)]
            print("hashes_parsed", hashes_parsed)
            applicants["raw"] = [file for file in files_for_matching if os.path.basename(file).split(".")[0] not in hashes_parsed]

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
        
        
        # Call the matching logic
        print("running pipeline")
        results_df, warnings = pipeline.run_multiple_cvs(requirement_path= tmp_path, 
                                                         cv_paths=applicants, 
                                                         args=weighted_config )
        
        #(pd.DataFrame({'applicants':applicants}), []) #call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants)

        if results_df is None:
            return JSONResponse(content={"error": "Error while extracting requirements! Check structure of requirements file and try again.", "warnings": warnings}, status_code=500)

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