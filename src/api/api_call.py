from fastapi import FastAPI, UploadFile, Form, File
from typing import List
from fastapi.responses import JSONResponse
import pandas as pd
import sys
import os
from typing import List


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from matching.match_applicants import match_applicant

app = FastAPI()

def call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n):
    results = match_applicant(requirements, exp_weight, pro_weight, per_weight, edu_weight, n)
    print(results)
    return results

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
        results_df = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n)
        
        # Return the results as JSON
        return JSONResponse(content={"results": results_df.to_dict(orient="records")})
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
