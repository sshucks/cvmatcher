import json
import hashlib
from fastapi import FastAPI, HTTPException, Form, UploadFile, File
from typing import List, Optional
from fastapi.responses import StreamingResponse
print("Before Google Import")
from google.cloud import storage
print("Google imported")
import io

print("Before API")
app = FastAPI()
print("FastAPI done")
client = storage.Client()
print("Client started")
pdf_bucket = "original-cvs-2410595"
json_bucket = "parsed-cvs-2410595"

@app.get("/get-cv-json")
def get_cv_json(hash:str):
    bucket = client.bucket(json_bucket)
    blob = bucket.blob(f"{hash}.json")  # path in GCS
    if not blob.exists():
        raise HTTPException(status_code=404, detail="JSON not found")

    json_bytes = blob.download_as_bytes()
    data = json.loads(json_bytes)  # parse bytes into Python dict
    return data


@app.get("/get-cv-pdf")
def get_cv_pdf(hash:str) -> StreamingResponse:
    bucket = client.bucket(pdf_bucket)
    blob = bucket.blob(f"{hash}.pdf")  # path in GCS
    pdf_bytes = blob.download_as_bytes()   # download file as bytes
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={hash}.pdf"}
    )

@app.post("/upload-json")
def upload_json(hash: str = Form(...), file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="File must be JSON")

    try:
        data = json.load(file.file)  # validate JSON
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    bucket = client.bucket(json_bucket)
    blob = bucket.blob(f"cvs/{hash}.json")
    blob.upload_from_string(json.dumps(data), content_type="application/json")

    return {"message": f"JSON uploaded as cvs/{hash}.json"}

@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be PDF")

    # Make sure file pointer is at start
    file.file.seek(0)

    # Compute hash
    hash_digest = hashlib.file_digest(file.file, "sha256").hexdigest()

    # Read file bytes for upload
    file.file.seek(0)
    file_bytes = file.file.read()

    # Save to GCS
    bucket = client.bucket(pdf_bucket)
    blob = bucket.blob(f"{hash_digest}.pdf")
    blob.upload_from_string(file_bytes, content_type="application/pdf")

    return {"file_hash": hash_digest, "message": f"PDF uploaded as {hash_digest}.pdf"}


@app.get("/get-all-jsons")
def get_all_jsons():
    bucket = client.bucket(json_bucket)
    blobs = bucket.list_blobs()  # list all JSON files in cvs/ folder

    all_data = []

    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue  # skip non-json files

        # Extract hash from filename
        # e.g., cvs/abc123.json -> abc123
        hash_value = blob.name.split("/")[-1].replace(".json", "")

        try:
            print("Found json in bucket")
            json_bytes = blob.download_as_bytes()
            data = json.loads(json_bytes)
            data["file_hash"] = hash_value
            all_data.append(data)
        except Exception as e:
            # Skip invalid JSON but log it
            print(f"Failed to read {blob.name}: {e}")
            continue

    if not all_data:
        raise HTTPException(status_code=404, detail="No JSON files found")

    return all_data