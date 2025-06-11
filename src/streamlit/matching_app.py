import streamlit as st
import pandas as pd
import requests

import sys
import os
import src.extracting.extraction_main as extraction
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- --- ---

st.title('CV Matcher')

col1, col2 = st.columns([1.5, 1])

cv_path = "input_cvs"

with col1:
    requirements = st.file_uploader('Upload requirements')
    # start new
    cvs = st.file_uploader('Upload cvs', accept_multiple_files=True, type=["pdf", "docx"])

    col1.write('## Matching results')

# end new


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
        # Prepare data for API call
        files = [("requirements", (requirements.name, requirements, requirements.type))]

        if cvs:
            for file in cvs:
                files.append(("input_cvs", (file.name, file, file.type)))


        data = {
            "edu_weight": edu_weight,
            "exp_weight": exp_weight,
            "pro_weight": pro_weight,
            "per_weight": per_weight,
            "n": number,
            "filename": requirements.name
        }

        response = requests.post("http://127.0.0.1:8000/process", files=files, data=data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            col1.dataframe(results, column_config={"E-Mail": st.column_config.LinkColumn(display_text="E-Mail")})

        else:
            col1.error(f"Error: {response.status_code} - {response.json().get('error')}")
    else:
        col1.error("Please upload a requirements file.")