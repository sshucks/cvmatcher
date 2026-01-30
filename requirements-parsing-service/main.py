import json
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/requirements-parsing")
def parse_cv_endpoint(requirements_file: UploadFile = File(...)) -> dict:
    # read json file alternatively process requirements file using llm
    content = requirements_file.file.read().decode("utf-8")
    requirements_data = json.loads(content)
    requirements_file.file.close()
    
    return requirements_data