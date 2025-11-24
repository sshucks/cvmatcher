from fastapi import FastAPI, UploadFile, Form, File, status
from typing import List
from fastapi.responses import JSONResponse
import sys
import os
from typing import List

from tqdm import tqdm
from typing import List, Optional


app = FastAPI()

# def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants):
#     results, warnings = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n, applicants)
#     return results, warnings


# def extract_cv(file_path, hash):
#     # make API call to extract information and store response JSON
#     output_file = os.path.join(CV_OUTPUT_DIR, f"{os.path.splitext(hash)[0]}.json")
#     process_cv_php(file_path, output_file)
        
#     read_json_file(output_file)


# @app.post("/process")
# async def process_matching(
#     requirements: UploadFile = File(...),
#     input_cvs: Optional[List[UploadFile]] = File(None),
#     all_cvs: bool = Form(...),
#     edu_weight: int = Form(...),
#     exp_weight: int = Form(...),
#     pro_weight: int = Form(...),
#     per_weight: int = Form(...),
#     n: int = Form(...)
# ):
#     """Accept a file containing a requirements description and optinaly some CVs and performing applicant matching


#     :param requirements: File containting the requirements for the position
#     :type requirements: UploadFile
#     :param input_cvs: List of CVs that are used in the scoring, if empty, whole database will be used
#     :type input_cvs: List[UploadFile]
#     :param all_cvs: whether to use all CVs in the database or only the provided input cvs
#     :type all_cvs: bool
#     :param edu_weight: weight of education
#     :type edu_weight: int
#     :param exp_weight: weight of working experience
#     :type exp_weight: int
#     :param pro_weight: weight of professional skills
#     :type pro_weight: int
#     :param per_weight: weight of personal skills
#     :type per_weight: int
#     :param n: number of top applicants to return
#     :type n: int
#     :return: list of top n applicants including score, age, email and birthdate
#     :rtype: JSON
#     """
#     try:
#         # compute provided CVs if present
#         if input_cvs:
#             # store and extract CVs in filesystem and calculate hash and insert into database
#             files_for_matching = await save_input_cvs(input_cvs)            
#         else:
#             print("No input cvs received")
        
#         # determine the applicants to score
#         applicants = None
#         if all_cvs:
#              # if the flag for all cvs is checked, use all CVs in database
#             applicants = os.listdir(CV_OUTPUT_DIR_MATCHING)
#             # remove non-json files
#             applicants = [file.removesuffix(".json") for file in applicants if file.endswith('.json')]
#         elif input_cvs: 
#             # if cvs are provided, use only provided CVs
#             applicants = files_for_matching
        
#         # if no CVs are provided and the all CVs flag is not checked, return errors
#         if not all_cvs and not input_cvs:
#             return JSONResponse(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 content={
#                     "results": None,
#                     "error": "Neither a list of CVs was provided nor the option to use all CVs in the database was checked. Please provide some CVs or check the option to use all CVs in the database."
#                 }
#             )
#         # Call the matching logic
#         results_df, warnings = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n, applicants)

#         if results_df is None:
#             return JSONResponse(content={"error": "Error while extracting requirements! Check structure of requirements file and try again.", "warnings": warnings}, status_code=500)

#         response = JSONResponse(content={
#             "results": results_df.to_dict(orient="records"),
#             "warnings": warnings or None  # Return None if empty
#         })

#         return response
#     except Exception as e:
#         print(e)
#         return JSONResponse(content={"error": str(e)}, status_code=500)
