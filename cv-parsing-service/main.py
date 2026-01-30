import json
from fastapi import FastAPI, UploadFile, Form, File, status
from typing import List, Optional

app = FastAPI()

@app.post("/cv-parsing")
def parse_cv_endpoint(cv_files:Optional[List[UploadFile]] = File(None), db_cvs: bool = Form(False)) -> List[dict]:
    
    # read cv json file alternatively process cv file using llm
    
    if db_cvs:
        # fetch from database TODO @Sigi
        pass
    
    # iterate over uploaded files
    cv_data = []
    for file in cv_files:
        content = file.file.read().decode("utf-8")
        
        file_hash = hash(content)
        cv_json = json.loads(content)
        
        cv_json["file_hash"] = file_hash
        
        cv_data.append(cv_json)
        file.file.close()
    
    return cv_data