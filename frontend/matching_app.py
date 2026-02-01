# --- Imports ---
import streamlit as st
import requests
import pandas as pd
import base64


# --- Settings ---
settings = {
    "acceptance-threshold": 0.7
}

# --- Utility Functions ---
def compute_status(score: float) -> str:
    threshold = float(settings.get("acceptance-threshold", 0.70))
    if score >= threshold:
        return "Accepted"
    return "Rejected"

def local_css(file_name):
    with open(file_name) as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def extract_column(row, col_path):
    parts = col_path.split('.')
    val = row
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p, None)
        else:
            return None
    return val

def request_cv_file_from_api(applicant_hash):
    # TODO @Sigi
    response = requests.get(
                    "http://data-access-service:8000/get-cv-pdf",
                    params={"hash": applicant_hash}  # pass query parameters correctly
                )
    
    if response.status_code == 200:
        pdf_bytes = response.content
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return base64_pdf
    
    return None

def process_matching(requirements, cvs, use_all_cvs, edu_weight, exp_weight, pro_weight, per_weight):
    weights = {
        "education": edu_weight,
        "professional_experience": exp_weight,
        "hard_skills": pro_weight,
        "soft_skills": per_weight,
    }
    with st.spinner("Processing matching..."):
        cv_files = [("cv_files", (cv.name, cv.getvalue(), cv.type)) for cv in cvs]
        parsed_cvs = requests.post(
            "http://cv-parsing-service:8000/cv-parsing",
            # "http://host.docker.internal:8001/cv-parsing",
            files=cv_files,
            data={"db_cvs": str(use_all_cvs).lower()}
        )
        parsed_requirements = requests.post(
            "http://requirements-parsing-service:8000/requirements-parsing",
            # "http://host.docker.internal:8002/requirements-parsing",
            files={"requirements_file": (requirements.name, requirements.getvalue(), requirements.type)}
        )
        if parsed_cvs.status_code != 200:
            st.error(f"Error parsing CVs: {parsed_cvs.status_code}")
            return None
        if parsed_requirements.status_code != 200:
            st.error(f"Error parsing requirements: {parsed_requirements.status_code}")
            return None
        parsed_cvs = parsed_cvs.json()
        parsed_requirements = parsed_requirements.json()
        matching_results = requests.post(
            "http://matching-service:8000/matching",
            # "http://host.docker.internal:8003/matching",
            json={"cv_data": parsed_cvs, "requirements": parsed_requirements, "weights": weights}
        )
        if matching_results.status_code == 200:
            
            # get file hash, name and email from parsed cvs and combine with matching results
            parsed_cvs_df = pd.DataFrame(parsed_cvs).set_index("file_hash")
            # Keep 'personal' and add file_hash as a column
            parsed_cvs_df = parsed_cvs_df[["personal"]]

            matching_results_df = pd.DataFrame(matching_results.json()).set_index("file_hash")
            combined_df = pd.concat([parsed_cvs_df, matching_results_df], axis=1)
            combined_df["status"] = combined_df["final_score"].apply(compute_status)

            combined_df = combined_df.reset_index()

            # order by final score
            combined_df = combined_df.sort_values(by="final_score", ascending=False)
            
            return combined_df
        else:
            st.error(f"Error processing matching: {matching_results.status_code}")
            return None

# --- Streamlit App ---
st.set_page_config(page_title="CV Matcher 🪄", layout="wide")
local_css("style.css")

# --- Session State ---
if "results" not in st.session_state:
    st.session_state["results"] = None
if "warnings" not in st.session_state:
    st.session_state["warnings"] = []
if "selected_index" not in st.session_state:
    st.session_state["selected_index"] = 0
if "parsed_cvs" not in st.session_state:
    st.session_state["parsed_cvs"] = None

# --- Layout ---
left_col, right_col = st.columns([1, 3])

def show_form():
    with st.form("cv_form"):
        st.markdown("## Upload CVs for Analysis")
        requirements = st.file_uploader("Upload requirements file")
        cvs = st.file_uploader("Upload CVs", accept_multiple_files=True)
        with st.expander("Configure importance"):
            cols = st.columns(2)
            edu_weight = cols[0].slider("Education", 0, 10, 5)
            exp_weight = cols[0].slider("Experience", 0, 10, 5)
            pro_weight = cols[1].slider("Professional Skills", 0, 10, 5)
            per_weight = cols[1].slider("Personal Skills", 0, 10, 3)
        use_all_cvs = st.toggle("Use all CVs in database")
        apply = st.form_submit_button("Process")
        return apply, requirements, cvs, use_all_cvs, edu_weight, exp_weight, pro_weight, per_weight

with left_col:
    apply, requirements, cvs, use_all_cvs, edu_weight, exp_weight, pro_weight, per_weight = show_form()

with right_col:
    if apply:
        if not requirements:
            st.error("Please upload a requirements file.")
        elif not cvs:
            st.error("Please upload at least one CV.")
        else:
            matching_results = process_matching(requirements, cvs, use_all_cvs, edu_weight, exp_weight, pro_weight, per_weight)
            if matching_results is not None:
                st.session_state["results"] = matching_results
            else:
                st.session_state["results"] = None

    results = st.session_state["results"]

    with st.container(border=True):
        st.markdown("## Matching Results")
        if results is None or (isinstance(results, (list, pd.DataFrame)) and len(results) == 0):
            st.info("No results yet.")
        else:
            # Convert results to list of dicts if needed
            if isinstance(results, str):
                import json
                data = json.loads(results)
            elif isinstance(results, pd.DataFrame):
                data = results.to_dict(orient="records")
            else:
                data = results
            columns_to_show = [
                ("personal.name", "Name"),
                ("personal.mail", "E-Mail"),
                ("final_score", "Match %"),
                ("status", "CV Status")
            ]
            # Build HTML table
            def percent_fmt(x):
                try:
                    return f"{float(x):.0%}" if x is not None else "N/A"
                except Exception:
                    return "N/A"
            table_html = "<table style='width:100%; border-collapse:collapse;'>"
            # Header
            table_html += "<tr>"
            for _, col_name in columns_to_show:
                table_html += f"<th style='border:1px solid #ccc; padding:6px; background:#f7f7f7'>{col_name}</th>"
            table_html += "</tr>"
            # Rows
            for row in data:
                # Extract columns
                row_vals = []
                for col_path, _ in columns_to_show:
                    if '.' in col_path:
                        val = extract_column(row, col_path)
                    else:
                        val = row.get(col_path, None)
                    row_vals.append(val)
                # Format Match %
                if row_vals[2] is not None:
                    row_vals[2] = percent_fmt(row_vals[2])
                # Make E-Mail a mailto link
                if row_vals[1]:
                    email = str(row_vals[1])
                    row_vals[1] = f"<a href='mailto:{email}'>{email}</a>"
                # Font color for Match % and CV Status
                match_color = ''
                status_color = ''
                status = row_vals[3]
                if status == "Accepted":
                    match_color = 'color: #218838; font-weight: bold;'
                    status_color = 'color: #218838; font-weight: bold;'
                elif status == "Rejected":
                    match_color = 'color: #c82333; font-weight: bold;'
                    status_color = 'color: #c82333; font-weight: bold;'
                table_html += "<tr>"
                for idx, val in enumerate(row_vals):
                    style = "border:1px solid #ccc; padding:6px"
                    if idx == 2:
                        style += f'; {match_color}'
                    if idx == 3:
                        style += f'; {status_color}'
                    table_html += f"<td style='{style}'>{val if val is not None else ''}</td>"
                table_html += "</tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

    # Details (card with PDF preview)
    with st.container(border=True):

        header_left, header_right = st.columns([1, 1])
        with header_left:
            st.markdown("## Details")
        with header_right:
            st.markdown("## CV Preview")

        if results is None:
            st.info("No candidate selected yet.")
        else:
            info_col, pdf_col = st.columns([1, 1])

            # LEFT COLUMN: select + summary + skills + experiences 
            with info_col:
                def get_row_name(row):
                    row.to_dict()
                    return row.get("personal", {}).get("name") or row.get("personal.name")
                    
                if hasattr(results, "iterrows"):
                    rows = [row for _, row in results.iterrows()]
                elif isinstance(results, list):
                    rows = results
                else:
                    rows = []

                names = [get_row_name(row) for row in rows if get_row_name(row)]
                if names:
                    default_index = st.session_state.get("selected_index", 0)
                    selected_name = st.selectbox("Select Candidate", names, index=default_index)
                    st.session_state["selected_index"] = names.index(selected_name)
                    selected = next(row for row in rows if get_row_name(row) == selected_name)
                    # Extract values
                    if isinstance(selected, dict):
                        sel_score = float(selected.get("final_score", 0))
                        sel_status = compute_status(sel_score)
                        sel_email = selected.get("personal", {}).get("mail") or selected.get("personal.mail") or selected.get("E-Mail") or selected.get("E_Mail") or ""
                        education = selected.get('education', 0)
                        professional_experience = selected.get('professional_experience', 0)
                        hard_skills = selected.get('hard_skills', 0)
                        soft_skills = selected.get('soft_skills', 0)
                    else:
                        d = selected.to_dict()
                        sel_score = float(d.get("final_score", 0))
                        sel_status = compute_status(sel_score)
                        sel_email = d.get("personal", {}).get("mail") or d.get("personal.mail") or d.get("E-Mail") or d.get("E_Mail") or ""
                        education = d.get('education', 0)
                        professional_experience = d.get('professional_experience', 0)
                        hard_skills = d.get('hard_skills', 0)
                        soft_skills = d.get('soft_skills', 0)

                    st.write(f"{selected_name} has a match score of **{sel_score:.0%}**.")
                    st.write(f"Current status: **{sel_status}**")

                    subscores = pd.DataFrame({
                        'Education': [f"{education:.0%}"],
                        'Professional Experience': [f"{professional_experience:.0%}"],
                        'Hard Skills': [f"{hard_skills:.0%}"],
                        'Soft Skills': [f"{soft_skills:.0%}"] ,
                    })
                    st.markdown(subscores.to_html(index=False), unsafe_allow_html=True)
                else:
                    st.info("No candidates available for selection.")


            # RIGHT COLUMN: CV Preview 
            with pdf_col:
                
                base64_pdf = request_cv_file_from_api(selected["file_hash"])

                pdf_html = f"""
                <iframe
                    src="data:application/pdf;base64,{base64_pdf}"
                    width="100%"
                    height="650"
                    style="border:none;"
                    type="application/pdf">
                </iframe>
                """

                st.markdown(pdf_html, unsafe_allow_html=True)
                

    # Warnings 
    # for w in st.session_state.get("warnings") or []:
    #     st.warning(w)