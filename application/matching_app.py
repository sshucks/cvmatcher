from pathlib import Path
import streamlit as st
from typing import TypedDict
import requests
import sys
import os
import base64
import json
import glob
from datetime import datetime
import matplotlib.pyplot as plt
from config import CSS_PATH
import base64
import pandas as pd
# Imports / paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from caching.models import CachedCVs
from caching import get_db


# Settings + History paths
BASE_DIR = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / "settings.json"
HISTORY_FILE = BASE_DIR / "match_history.json"

def local_css(file_name):
    with open(file_name) as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
        

def get_settings() -> dict:
    # Get current application settings from API
    with st.spinner("Loading settings..."):
        response = requests.get("http://127.0.0.1:8000/settings")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching settings: {response.status_code}")
            return {}

def save_settings(settings: dict) -> None:
    with st.spinner("Saving settings..."):
        response = requests.post("http://127.0.0.1:8000/settings", json=settings)
        if response.status_code == 200:
            print("Settings saved successfully.")
        else:
            print(f"Error saving settings: {response.status_code}")


settings = get_settings()

# History helpers (file-based)
def load_history() -> list[dict]:
    response = requests.get("http://127.0.0.1:8000/history")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching history: {response.status_code}")
        return []

def clear_history() -> None:
    # Clear history file content (reset to empty list).
    response = requests.delete("http://127.0.0.1:8000/history")
    if response.status_code == 200:
        print("History cleared successfully.")
    else:
        print(f"Error clearing history: {response.status_code}")


MIME_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".rtf": "application/rtf",
}


def get_mime_type(filename: str) -> str:
    # Return the MIME type for a given filename based on its extension.
    # If it cannot be determined, return application/octet-stream.
    if not filename:
        return "application/octet-stream"
    _, ext = os.path.splitext(filename)
    return MIME_TYPES.get(ext.lower(), "application/octet-stream")


def create_download_link(hash: str, label: str) -> str:
    # Build an HTML download link for a file by base64-encoding its content.
    # Used to allow CV download directly in the browser.
    
    return f"<a href='http://127.0.0.1:8000/get_cv/{hash}?download=true' class='cv-button'>{label}</a>"

def request_cv_file_from_api(cv_hash: str, download:bool = False) -> dict | None:
    # Request parsed CV data from API by hash
    with st.spinner(f"Retrieving PDF version of CV..."):
        response = requests.get(f"http://127.0.0.1:8000/get_cv/{cv_hash}?download=false")
        
        if response.status_code == 200:
            print(f"Successfully fetched CV with hash {cv_hash} from API.")
            print(f"Response content size: {len(response.content)} bytes")
            print(f"Response headers: {response.headers}")
            base64_pdf = base64.b64encode(response.content).decode('utf-8')
            return base64_pdf
        
        else:
            print(f"Error fetching CV with hash {cv_hash}: {response.status_code}")
            return None
        
def process_matching() -> requests.Response:
    # Send matching request to API
    with st.spinner("Processing matching..."):
        response = requests.post("http://127.0.0.1:8000/process", files=files, data=data)

        if response.status_code == 200:
            print("Matching processed successfully.")
            return response
        else:
            print(f"Error processing matching: {response.status_code}")
        return {}

st.set_page_config(page_title="CV Matcher 🪄", layout="wide")


class PersonRecord(TypedDict):
    Name: str
    Score: float
    Birthdate: str | None
    Filename: str
    E_Mail: str


local_css(CSS_PATH)

# CSS + NAVBAR
st.markdown(
    """
<div class="navbar">
    <div class="nav-title">CV Matcher 🪄</div>
    <div class="nav-links">
        <a class="nav-link" href="?page=main" target="_self">Home</a>
        <a class="nav-link" href="?page=analyses" target="_self">Analyses</a>
        <a class="nav-link" href="?page=settings" target="_self">Settings</a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Which page are we on?
params = st.query_params
raw_page = params.get("page", "main")
if isinstance(raw_page, list):
    page = raw_page[0]
else:
    page = raw_page

# GLOBAL STATE 
if "results" not in st.session_state:
    st.session_state["results"] = []
if "warnings" not in st.session_state:
    st.session_state["warnings"] = []
if "selected_index" not in st.session_state:
    st.session_state["selected_index"] = 0



def compute_status(score: float) -> str:
    # Map a numerical score to Accepted / Rejected using threshold settings 
    threshold_cfg = settings.get("Threshold", {})
    threshold = float(threshold_cfg.get("value", 0.70))
    if score >= threshold:
        return "Accepted"
    return "Rejected"



# PAGE ROUTING
if page == "settings":
    # SETTINGS PAGE 

    left_spacer, mid, right_spacer = st.columns([1, 2, 1])

    with mid:
        st.markdown('<div class="settings-title">Settings</div>', unsafe_allow_html=True)

        
        llm_cfg = settings.get("LLM", {})
        thr_cfg = settings.get("Threshold", {})

        llm_value = llm_cfg.get("value", "lamms3.1:8b")
        thr_value = float(thr_cfg.get("value", 0.70))
        thr_min = float(thr_cfg.get("min", 0.0))
        thr_max = float(thr_cfg.get("max", 1.0))
        thr_step = float(thr_cfg.get("step", 0.01))

        with st.form("settings_form"):
            st.text("Global settings for the matching pipeline:")

            new_llm = st.text_input("LLM Model", value=str(llm_value))
            
            new_thr = st.number_input(
                "Acceptance Threshold",
                min_value=thr_min,
                max_value=thr_max,
                step=thr_step,
                value=thr_value,
            )

            saved = st.form_submit_button("Save settings")

        if saved:
            if "LLM" in settings:
                settings["LLM"]["value"] = new_llm
            if "Threshold" in settings:
                settings["Threshold"]["value"] = float(new_thr)

            save_settings(settings)
            st.success("Settings saved. Please run matching again to apply changes.")
elif page == "analyses":
    # ANALYSES / DASHBOARD
    st.subheader("Analyses – History & Dashboard")

    if st.button("Clear History 🗑️"):
        clear_history()
        st.success("History cleared.")

    history = load_history()

    if not history:
        st.info("No analyses yet. Run a matching on Home first.")
    else:
        summary_rows = [
            {
                "Run": i + 1,
                "Time": h.get("time", ""),
                "Req. File": h.get("requirements_file", ""),
                "CVs": h.get("num_cvs", 0),
                "Accepted": h.get("accepted", 0),
                "Rejected": h.get("rejected", 0),
            }
            for i, h in enumerate(history)
        ]

        col_table, col_chart = st.columns([2, 1.2])

        # History table
        with col_table:
            table_html = """
<table class="match-table">
<tr>
<th>Run</th>
<th>Time</th>
<th>Req. File</th>
<th>CVs</th>
<th>Accepted</th>
<th>Rejected</th>
</tr>
"""
            for row in summary_rows:
                table_html += f"""
<tr>
<td>{row["Run"]}</td>
<td>{row["Time"]}</td>
<td>{row["Req. File"]}</td>
<td>{row["CVs"]}</td>
<td>{row["Accepted"]}</td>
<td>{row["Rejected"]}</td>
</tr>
"""
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)

        #Pie char
        with col_chart:
            idx = st.selectbox(
                "Select a run to show pie chart:",
                options=list(range(len(history))),
                format_func=lambda i: f'Run {i+1} – {history[i].get("time","")}',
            )

            run = history[int(idx)]
            labels = ["Accepted", "Rejected"]
            sizes = [run.get("accepted", 0), run.get("rejected", 0)]

            if sum(sizes) > 0:
                fig, ax = plt.subplots(figsize=(2.3, 2.3), dpi=110)

                plt.rcParams["font.size"] = 7
                plt.rcParams["font.family"] = "DejaVu Sans"

                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=None,  
                    autopct="%1.0f%%",
                    startangle=90,
                    colors=["#2ECC71", "#E74C3C"],
                    textprops={"fontsize": 7, "color": "white"},
                )

                ax.legend(
                    wedges,
                    labels,
                    title="CV Status",
                    loc="center left",
                    bbox_to_anchor=(1.05, 0.5),
                    fontsize=8,
                    title_fontsize=9,
                )

                ax.set_title("CV Status Distribution", fontsize=10, pad=5)
                ax.axis("equal")

                plt.tight_layout()
                st.pyplot(fig, use_container_width=False)

# PAGE: MAIN / MATCHING
else:
    left_col, right_col = st.columns([1, 3])

    # LEFT PANEL — FORM
    with left_col:
        with st.form("cv_form"):
            st.markdown("## Upload CVs for Analysis")

            requirements = st.file_uploader("Upload requirements file")
            cvs = st.file_uploader("Upload CVs", accept_multiple_files=True)

            with st.expander("Configure importance"):
                cols = st.columns(4)
                edu_weight = cols[0].slider("Education", 0, 10, 5)
                exp_weight = cols[1].slider("Experience", 0, 10, 5)
                pro_weight = cols[2].slider("Professional Skills", 0, 10, 5)
                per_weight = cols[3].slider("Personal Skills", 0, 10, 3)

                use_all_cvs = st.toggle("Use all CVs in database")
                number = st.number_input(
                    "Results shown", min_value=1, max_value=100, value=10
                )

            col_left, col_right = st.columns([5, 2])
            with col_right:
                apply = st.form_submit_button("Process")

    # RIGHT PANEL — RESULTS + DETAILS
    with right_col:
        # ---- Process request ----
        if apply:
            if not requirements:
                st.error("Please upload a requirements file.")
            else:
                files = [
                    ("requirements", (requirements.name, requirements, requirements.type))
                ]

                if cvs:
                    for file in cvs:
                        files.append(("input_cvs", (file.name, file, file.type)))

                data = {
                    "edu_weight": edu_weight,
                    "exp_weight": exp_weight,
                    "pro_weight": pro_weight,
                    "per_weight": per_weight,
                    "n": number,
                    "filename": requirements.name,
                    "all_cvs": use_all_cvs,
                }

                matching_results = process_matching()

                if matching_results:
                    payload = matching_results.json()
                    results = payload.get("results", []) or []
                    st.session_state["results"] = results
                    try:
                        st.session_state["warnings"] = payload.get("warnings", []) or []
                    except Exception:
                        st.session_state["warnings"] = []

                    if results:
                        accepted = rejected = 0
                        for r in results:
                            s = compute_status(float(r["Score"]))
                            if s == "Accepted":
                                accepted += 1
                            else:
                                rejected += 1
                
                    else:
                        st.warning("Process returned no results.")
                else:
                    st.session_state["results"] = []
                    st.session_state["warnings"] = []
                    st.error(f"Error: {matching_results.status_code}")

        results = st.session_state["results"]

        # Matching Results (top-right card)
        with st.container(border=True):
            st.markdown("## Matching Results")

            if not results:
                st.info("No results yet.")
            else:
                table_html = """
<table class="match-table">
<tr>
<th>Name</th>
<th>E-Mail</th>
<th>Match %</th>
<th>CV Status</th>
<th>CV</th>
</tr>
"""

                threshold = float(settings.get("Threshold", {}).get("value", 0.70))
                for r in results:
                    score = float(r["Score"])
                    score_str = f"{score:.0%}"

                    # Match% coloring (independent of CV Status)

                    if score >= threshold:
                        score_class = "match-green"
                    else:
                        score_class = "match-red"

                    stat = compute_status(score)
                    stat_class = "match-green" if stat == "Accepted" else "match-red"

                    email = r.get("E-Mail") or r.get("E_Mail") or ""

                    download_btn = (
                        create_download_link(r['applicant_hash'], "Download CV")
                    )

                    table_html += f"""
<tr>
<td>{r['Name']}</td>
<td><a href=\"mailto:{email}\" target=\"_blank\">{email}</a></td>
<td class="{score_class}">{score_str}</td>
<td class="{stat_class}">{stat}</td>
<td>{download_btn}</td>
</tr>
"""

                table_html += "</table>"

                st.markdown(table_html, unsafe_allow_html=True)

        # Details (card with PDF preview)
        with st.container(border=True):

            header_left, header_right = st.columns([1, 1])
            with header_left:
                st.markdown("## Details")
            with header_right:
                st.markdown("## CV Preview")

            if not results:
                st.info("No candidate selected yet.")
            else:
                info_col, pdf_col = st.columns([1, 1])

                # LEFT COLUMN: select + summary + skills + experiences 
                with info_col:
                    names = [r["Name"] for r in results]
                    default_index = st.session_state.get("selected_index", 0)
                    if default_index >= len(names):
                        default_index = 0

                    selected_name = st.selectbox(
                        "Select a candidate to see details:",
                        names,
                        index=default_index,
                    )
                    st.session_state["selected_index"] = names.index(selected_name)

                    selected = next(r for r in results if r["Name"] == selected_name)
                    sel_score = float(selected["Score"])
                    sel_status = compute_status(sel_score)
                    sel_email = selected.get("E-Mail") or selected.get("E_Mail") or ""

                    st.write(
                        f"{selected_name} has a match score of **{sel_score:.0%}**."
                    )
                    st.write(f"Current status: **{sel_status}**")
                    if sel_email:
                        mailto_link = f"[{sel_email}](mailto:{sel_email})"
                        st.write(f"Contact: {mailto_link}")
                

                    subscores = pd.DataFrame({
                        'Education': [ f"{score:.0%}" for score in [selected.get('education', 0)]],
                        'Professional Experience': [ f"{score:.0%}" for score in [selected.get('professional_experience', 0)]],
                        'Hard Skills': [ f"{score:.0%}" for score in [selected.get('hard_skills', 0)]],
                        'Soft Skills': [ f"{score:.0%}" for score in [selected.get('soft_skills', 0)]] ,
                        })
                    
                    print(f"Subscores DataFrame:\n{subscores}")
                    st.markdown(subscores.to_html(index=False), unsafe_allow_html=True)


                # RIGHT COLUMN: CV Preview 
                with pdf_col:
                    
                    base64_pdf = request_cv_file_from_api(selected["applicant_hash"])

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
        for w in st.session_state.get("warnings") or []:
            st.warning(w)