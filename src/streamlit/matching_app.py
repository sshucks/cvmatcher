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

# Imports / paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from caching.models import CachedCVs
from caching import get_db


# Settings + History paths
BASE_DIR = Path(__file__).parent
SETTINGS_FILE = BASE_DIR / "settings.json"
HISTORY_FILE = BASE_DIR / "match_history.json"


def load_settings() -> dict:
    # Load settings from settings.json 
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_settings(settings: dict) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


settings = load_settings()

# History helpers (file-based)
def load_history() -> list[dict]:
    # Read run-history list from match_history.json
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception as e:
            print("ERROR reading history:", e)
            return []
    return []


def append_history(entry: dict) -> None:
    # Append one run-summary to history file.
    hist = load_history()
    hist.append(entry)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("ERROR writing history:", e)


def clear_history() -> None:
    # Clear history file content (reset to empty list).
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
    except Exception as e:
        print("ERROR clearing history:", e)


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


def create_download_link(file_path: str, label: str) -> str:
    # Build an HTML download link for a file by base64-encoding its content.
    # Used to allow CV download directly in the browser.
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    mime = get_mime_type(file_path)
    fname = os.path.basename(file_path)
    return f'<a href="data:{mime};base64,{b64}" download="{fname}" class="cv-button">{label}</a>'


st.set_page_config(page_title="CV Matcher 🪄", layout="wide")

STORAGE_DIR = Path("input_cvs")
STORAGE_DIR.mkdir(exist_ok=True)


class PersonRecord(TypedDict):
    Name: str
    Score: float
    Birthdate: str | None
    Filename: str
    E_Mail: str



# CSS + NAVBAR
st.markdown(
    """
<style>

.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 2rem;
    background-color: #ffffff;
    border-bottom: 1px solid #eaeaea;
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-title {
    font-size: 2rem;
    font-weight: 800;
    color: #1A1A1A;
    font-family: 'Segoe UI', sans-serif;
}

.nav-links {
    display: flex;
    gap: 25px;
}

.nav-link {
    font-size: 1.05rem;
    font-weight: 600;
    color: #284AA3;
    text-decoration: none;
}

.nav-link:hover {
    color: #1f3a82;
}

.match-green { color: #2ECC71; font-weight: 600; }
.match-orange { color: #F39C12; font-weight: 600; } /* for Match % only */
.match-red { color: #E74C3C; font-weight: 600; }

.match-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 18px;
}

.match-table th, .match-table td {
    border: 1px solid #dcdcdc;
    padding: 10px;
    font-size: 0.9rem;
}

.match-table th {
    background-color: #f2f2f2;
    font-weight: 700;
}

.cv-button {
    background-color: #284AA3;
    color: white !important;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none !important;
    font-weight: 600;
    font-size: 0.9rem;
}

.cv-button:hover {
    background-color: #1f3a82;
    color: white !important;
}

button[kind="formSubmit"],
.stButton > button,
div.stForm button,
button[type="submit"] {
    background-color: #284AA3 !important;
    color: white !important;
    border: none !important;
    padding: 10px 22px !important;
    border-radius: 6px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

button[kind="formSubmit"]:hover,
.stButton > button:hover,
div.stForm button:hover,
button[type="submit"]:hover {
    background-color: #1f3a82 !important;
}

.skill-row {
    margin-bottom: 10px;
    max-width: 50%;
}

.skill-name {
    font-weight: 500;
    margin-bottom: 2px;
}

.skill-bar-outer {
    width: 100%;
    background-color: #e5e5e5;
    border-radius: 999px;
    height: 8px;
    overflow: hidden;
}

.skill-bar-inner {
    height: 100%;
    border-radius: 999px;
}

.skill-bar-inner.high { background-color: #2ECC71; }
.skill-bar-inner.medium { background-color: #F39C12; }
.skill-bar-inner.low { background-color: #E74C3C; }

div[data-testid="stSelectbox"] > div {
    max-width: 50%;
}

div[data-testid="stForm"] { margin-top: 0 !important; }
div[data-testid="stVerticalBlock"] { padding-top: 0 !important; }
div[data-testid="column"] { margin-top: 15px !important; }


/* ================================
   FILE UPLOADER PAGINATION (Home)
   ================================ */

div[data-testid="stFileUploaderPagination"] > button {
    margin: 0 !important;
    padding: 6px 14px !important;
    border-radius: 6px !important;
}

div[data-testid="stFileUploaderPagination"] > button:first-of-type {
    margin-right: 10px !important;  
}


/* ================================
      NUMBER INPUT BUTTONS (Settings)
   ================================ */

div[data-testid="stNumberInput"] > button {
    margin: 0 !important;
    padding: 3px 10px !important;
    border-radius: 4px !important;
}

div[data-testid="stNumberInput"] > button:first-of-type {
    margin-bottom: 4px !important;  
}

</style>

<div class="navbar">
    <div class="nav-title">CV Matcher 🪄</div>
    <div class="nav-links">
        <a class="nav-link" href="?page=main">Home</a>
        <a class="nav-link" href="?page=analyses">Analyses</a>
        <a class="nav-link" href="?page=settings">Settings</a>
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



# Helpers
def _get_cv_path(filename: str) -> str | None:
    # Get stored CV file path from DB (by original filename)
    with get_db() as db:
        return (
            db.query(CachedCVs.path)
            .filter(CachedCVs.file_name == filename)
            .scalar()
        )


def load_candidate_details(filename: str):
    # Read processed JSON for a candidate from extracted_cvs_matching
    pdf_path = _get_cv_path(filename)
    if not pdf_path:
        return None

    # file_hash is the stem of the pdf path, used as prefix for processed JSON
    file_hash = os.path.splitext(os.path.basename(pdf_path))[0]
    pattern = os.path.join("extracted_cvs_matching", f"{file_hash}_processed.json")
    matches = glob.glob(pattern)
    if not matches:
        return None

    json_path = matches[0]
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def build_summary(details: dict) -> str:
    # Create a short textual summary for a candidate
    p = details.get("personal_data", {})
    emps = details.get("employments", [])

    firstname = (p.get("firstname") or "").strip()
    surname = (p.get("surname") or "").strip()
    full_name = " ".join(x for x in [firstname, surname] if x) or "This candidate"

    positions = [e.get("position", "").title() for e in emps if e.get("position")]
    if positions:
        main_pos = positions[0]
        others = ", ".join(positions[1:3])
        if others:
            return f"{full_name} has experience as {main_pos}. Previous roles include {others}."
        else:
            return f"{full_name} has experience as {main_pos}."
    else:
        return f"{full_name} has professional experience relevant to this position."


def extract_top_skills(details: dict, top_n: int = 3):
    # Return a list of the top N non-role skills with scores
    skills_raw = details.get("skills", []) or []
    role_keywords = [
        "entwickl",
        "ingenieur",
        "manager",
        "leiter",
        "leitung",
        "consultant",
    ]
    bad_substrings = ["bachelor", "master", "degree", "diplom", "industry~"]

    level_map = {
        "EXCELLENT": 0.95,
        "WORKING": 0.8,
        "BASIC": 0.6,
    }

    items: list[tuple[str, float]] = []

    for s in skills_raw:
        names = s.get("skill_name") or []
        if not names:
            continue
        name = next((n for n in names if n), None)
        if not name:
            continue

        nl = name.lower()
        if any(k in nl for k in role_keywords):
            continue
        if any(b in nl for b in bad_substrings):
            continue

        lvl = (s.get("skill_level") or "").upper()
        score = level_map.get(lvl, 0.6)
        items.append((name, score))

    if not items:
        return []

    items.sort(key=lambda x: x[1], reverse=True)
    return items[:top_n]


def render_skill_bar(skill_name: str, score: float):
    # Render a horizontal bar with a color depending on score
    pct = max(0, min(100, int(score * 100)))

    if score >= 0.8:
        level_class = "high"
    elif score >= 0.5:
        level_class = "medium"
    else:
        level_class = "low"

    st.markdown(
        f"""
        <div class="skill-row">
            <div class="skill-name">{skill_name}</div>
            <div class="skill-bar-outer">
                <div class="skill-bar-inner {level_class}" style="width:{pct}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    st.markdown(
        """
        <style>
        section.main > div.block-container{
            padding-top: 0.5rem !important;
        }
        h2, h3{
            margin-top: 0.2rem !important;
            padding-top: 0 !important;
        }

        div[data-testid="stForm"]{
            max-width: 700px;
            margin: 0 auto !important;
        }

        /* Settings texts LEFT */
        div[data-testid="stForm"]{
            direction: ltr;
            text-align: left;
        }
        div[data-testid="stForm"] label{
            width: 100%;
            text-align: left !important;
        }
        div[data-testid="stForm"] input,
        div[data-testid="stForm"] textarea{
            direction: ltr;
            text-align: left;
        }

        div[data-testid="stFormSubmitButton"]{
            display: flex !important;
            justify-content: flex-end !important;
        }

        .settings-title{
            max-width: 700px !important;
            margin: 0 auto 0.2rem auto !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
            line-height: 1.1 !important;
            text-align: left !important;
        }

        div[data-testid="stForm"]{
            margin-top: 0rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    left_spacer, mid, right_spacer = st.columns([1, 2, 1])

    with mid:
        st.markdown(
            """
            <style>
            div[data-testid="stAppViewContainer"] section.main h2{
                margin-bottom: 0rem !important;
                padding-bottom: 0 !important;
            }
            div[data-testid="stForm"]{
                margin-top: 0rem !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

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

    st.caption(f"History file path: {HISTORY_FILE}")

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

                res = requests.post(
                    "http://127.0.0.1:8000/process", files=files, data=data
                )

                if res.status_code == 200:
                    payload = res.json()
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

                        append_history(
                            {
                                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "requirements_file": requirements.name,
                                "num_cvs": len(results),
                                "accepted": accepted,
                                "rejected": rejected,
                            }
                        )
                    else:
                        st.warning("Process returned no results.")
                else:
                    st.session_state["results"] = []
                    st.session_state["warnings"] = []
                    st.error(f"Error: {res.status_code}")

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

                    cvp = _get_cv_path(r["Filename"])
                    download_btn = (
                        create_download_link(cvp, "Download CV")
                        if cvp and os.path.exists(cvp)
                        else "N/A"
                    )

                    table_html += f"""
<tr>
<td>{r['Name']}</td>
<td>{email}</td>
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

                    details = load_candidate_details(selected["Filename"])

                    # Summary
                    if not details:
                        st.write(
                            f"{selected_name} has a match score of **{sel_score:.0%}**."
                        )
                        st.write(f"Current status: **{sel_status}**")
                        if sel_email:
                            st.write(f"Contact: `{sel_email}`")
                    else:
                        summary_text = build_summary(details)
                        st.write(summary_text)

                    # Top Skills
                    st.markdown("### Top Skills")
                    if details:
                        top_skills = extract_top_skills(details, top_n=3)
                        if top_skills:
                            for skill_name, score in top_skills:
                                render_skill_bar(skill_name, score)
                        else:
                            st.write("No skills found.")
                    else:
                        st.write("No skills found.")

                    # Top Experiences
                    st.markdown("### Top Experiences")
                    if details:
                        exps = [
                            e.get("position")
                            for e in details.get("employments", [])
                            if e.get("position")
                        ]
                        if exps:
                            for exp in exps[:3]:
                                st.markdown(f"- {exp}")
                        else:
                            st.write("No experiences found.")
                    else:
                        st.write("No experiences found.")

                # RIGHT COLUMN: CV Preview 
                with pdf_col:
                    cv_path = _get_cv_path(selected["Filename"])
                    if cv_path and os.path.exists(cv_path):
                        try:
                            ext = os.path.splitext(cv_path)[1].lower()

                            if ext != ".pdf":
                                st.info(
                                    f"Inline preview is only available for PDF CVs. "
                                    f"This CV is a *{ext}* file. Please download it to view."
                                )
                                st.markdown(
                                    create_download_link(cv_path, "Download CV"),
                                    unsafe_allow_html=True,
                                )
                            else:
                                with open(cv_path, "rb") as f:
                                    pdf_bytes = f.read()
                                base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

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
                        except Exception as e:
                            st.error(f"Could not display CV preview: {e}")
                    else:
                        st.info("No CV file found for this candidate.")

        # Warnings 
        for w in st.session_state.get("warnings") or []:
            st.warning(w)