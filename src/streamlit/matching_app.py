import streamlit as st
import pandas as pd
import requests
import unicodedata

import sys
import os
import src.extracting.extraction_main as extraction
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".rtf": "application/rtf",
    # Add other types as necessary
}

def get_mime_type(filename):
    """Determines the MIME type based on the file extension."""
    if not filename:
        return "application/octet-stream" # Default for unknown or missing filename

    # Get the file extension (e.g., '.pdf', '.docx')
    _, ext = os.path.splitext(filename)
    ext = ext.lower() # Convert to lowercase for consistent lookup

    # Look up the MIME type in our dictionary
    return MIME_TYPES.get(ext, "application/octet-stream") # Default to generic binary if not found


# --- --- ---
st.set_page_config(layout="wide")
st.title('CV Matcher')

col1, col2, col3 = st.columns([0.75, 0.75, 1.5])
col1.write("## File Uploads")
col2.write("## Parameters")
col3.write("## Matching Results")

col1_1, col1_2 = col1.columns(2)

cv_path = "input_cvs"

with col1:
    requirements = st.file_uploader(label="Upload requirements", type=['doc','docx'])
    cvs = st.file_uploader("CVs", accept_multiple_files=True, type=['doc','docx', "pdf"])


with col2:
    with st.form('Configure importance'):
        edu_weight = st.slider('Education', 0, 10, 5)
        exp_weight = st.slider('Experience', 0, 10, 5)
        pro_weight = st.slider('Professional Skills', 0, 10, 5, help='MS Office, ...', label_visibility='visible')
        per_weight = st.slider('Personal Skills', 0, 10, 3, help='Communication, ...', label_visibility='visible')

        number = st.number_input('Results shown', min_value=1, max_value=100, value=10, help='Number of best matches shown', label_visibility='visible')

        apply = st.form_submit_button('Apply')




if apply:
    if requirements:
        
        files_to_send = [
            ("requirements", (requirements.name, requirements.getvalue(), get_mime_type(requirements.name))) # Ensure content type matches
        ]

        # For the list of CVs, create a list of tuples
        cv_files_list = []
        for cv_file in cvs:
            print("in cv file loop")
            cv_filename = unicodedata.normalize('NFD', cv_file.name).encode('ascii', 'ignore').decode('utf-8')

            cv_files_list.append(('cvs', (cv_filename, cv_file.getvalue(), get_mime_type(cv_file.name)))) # Ensure content type matches

        files_to_send.extend(cv_files_list)
        
        # Prepare data for API call
        files = {"requirements": requirements.getvalue()}
        data = {
            "edu_weight": edu_weight,
            "exp_weight": exp_weight,
            "pro_weight": pro_weight,
            "per_weight": per_weight,
            "n": number,
            "filename": requirements.name
        }   
        
        print([f"{f[0]} - {f[1][0]}: {f[1][2]}" for f in files_to_send])

        response = requests.post("http://127.0.0.1:8000/process", files=files,   data=data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            col1.dataframe(results)
        else:
            col1.error(f"Error: {response.status_code} - {response.json().get('error')}")
    else:
        col1.error("Please upload a requirements file.")