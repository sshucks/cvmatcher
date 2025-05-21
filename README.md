# SPD2_TRESCON: CV_Matcher

This projects aims to match the best applicants to a job description based on their CV.

## Setup

### Requirements
Download and Install Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/
Download and Install VSCode: https://code.visualstudio.com/download

Install the following VSCode Extension: ms-vscode-remote.remote-containers


### Checkout Repository
If you have problems with authentication use GitHub Desktop to clone repository.

```
git clone https://github.com/sshucks/cvmatcher
cd cvmatcher
code .
```

Make sure that Docker Desktop is running.
Open Folder cvmatcher in VS Code and click “Reopen in Container” when prompted, or press Ctrl + Shift + P, then select “Dev Containers: Reopen in Container” from the command palette.

## Run Project

Put example CVs in *input_cvs*
If necessary delete already parsed CVs from
<ul>
    <li>extracted_cvs</li>
    <li>extracted_cvs_matching</li>
<ul>

### Process CVs
```
python src/extracting/extraction_main.py
```

### Start FastAPI
```
python -m fastapi dev src/api/api_call.py
```

### Start Streamlit App
```
python -m streamlit run src/streamlit/matching_app.py
```