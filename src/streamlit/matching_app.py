import streamlit as st
import pandas as pd
import requests

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- --- ---

st.title('CV Matcher')

col1, col2 = st.columns([1.5, 1])

with col1:
    requirements = st.file_uploader('Upload requirements')


with col2:
    with st.form('Configure importance'):
        edu_weight = st.slider('Education', 0, 10, 5)
        exp_weight = st.slider('Experience', 0, 10, 5)
        pro_weight = st.slider('Professional Skills', 0, 10, 5, help='MS Office, ...', label_visibility='visible')
        per_weight = st.slider('Personal Skills', 0, 10, 3, help='Communication, ...', label_visibility='visible')

        number = st.number_input('Results shown', min_value=1, max_value=100, value=10, help='Number of best matches shown', label_visibility='visible')

        apply = st.form_submit_button('Apply')


col1.write('## Matching results')

if apply:
    if requirements:
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

        response = requests.post("http://127.0.0.1:8000/process", files=files, data=data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            st.dataframe(results, column_config={"E-Mail": st.column_config.LinkColumn()})
            #results['E-Mail'] = results.apply(
             #                           lambda row: '<a href="{}">{}</a>'.format(row['E-Mail'], row['E-Mail']),
              #                          axis=1)
        else:
            col1.error(f"Error: {response.status_code} - {response.json().get('error')}")
    else:
        col1.error("Please upload a requirements file.")