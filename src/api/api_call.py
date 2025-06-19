from fastapi import FastAPI, UploadFile, Form, File
from typing import List
from fastapi.responses import JSONResponse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_applicants import match_applicant


app = FastAPI()

def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n):
    results, warnings = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n)

    return results, warnings

def save_input_cvs(input_cvs):
    for cv in input_cvs:
        file_path = os.path.join("input_cvs", cv.filename)
        with open(file_path, "wb") as f:
            f.write(cv.file.read())
    return 


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
    try:
        # Simulate processing the uploaded file
        print([i.filename for i in input_cvs])
        save_input_cvs(input_cvs)
        print(f"Received file: {requirements.filename}")
        #file_content = await requirements.read()

        # Call the matching logic
        results_df, warnings = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n)

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
