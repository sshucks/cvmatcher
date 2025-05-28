from fastapi import FastAPI, UploadFile, Form, File
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


@app.post("/process")
async def process_matching(
    requirements: UploadFile = File(...),
    #files: list[UploadFile]|None = File(...),
    edu_weight: int = Form(...),
    exp_weight: int = Form(...),
    pro_weight: int = Form(...),
    per_weight: int = Form(...),
    n: int = Form(...)
):
    try:
        print("In server")
        # Simulate processing the uploaded file
        print(f"Received file: {requirements.filename}")
        #print([f.filename for f in files])
        
        #file_content = await requirements.read()

        # Call the matching logic
        #results_df = call_matching(requirements, edu_weight, exp_weight, pro_weight, per_weight, n)
        
        return JSONResponse(content={"results":pd.DataFrame({'test': ['test', 'test3', 'test4']}).to_dict()})

        # Return the results as JSON
        return JSONResponse(content={"results": results_df.to_dict(orient="records")})
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
