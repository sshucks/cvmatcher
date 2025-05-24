# SPD2_TRESCON: CV_Matcher

This projects aims to match the best applicants to a job description based on their CV.

## Contribute to this project using VS Code

### Setup

#### Requirements
Download and Install Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/

Download and Install VSCode: https://code.visualstudio.com/download
Install the following VSCode Extension: ms-vscode-remote.remote-containers


#### Checkout Repository
If you have problems with authentication use GitHub Desktop to clone repository.

```
git clone https://github.com/sshucks/cvmatcher
cd cvmatcher
code .
```

### Start Devcontainer in VS Code
Make sure that Docker Desktop is running.
Open Folder cvmatcher in VS Code and click “Reopen in Container” when prompted, or press Ctrl + Shift + P, then select “Dev Containers: Reopen in Container” from the command palette.

The API and Streamlit-App start automatically right after building the container. Note that there is some more wait time included in starting the API. After both applications have started successfully, the application can be accessed at http://localhost:8501/

#### Process CVs
```
python src/extracting/extraction_main.py
```

#### Start FastAPI
```
python -m fastapi dev src/api/api_call.py
```

#### Start Streamlit App
```
python -m streamlit run src/streamlit/matching_app.py
```


## Run the application

### Setup

#### Requirements
Download and Install Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/

#### Get Source Code
Either clone the repository like this
```
git clone https://github.com/sshucks/cvmatcher
cd cvmatcher
```
or unzip the downloaded source code in your desired workspace.

#### Build Docker Container
Make sure that Docker Desktop is running, then open a terminal in the directory *cv_matcher* and run the following command to build the docker container. 

```
docker build -f .devcontainer/Dockerfile -t cvmatcher-dev .
```

This can take quite a long time (up to 20 minutes) and only needs to be done once. Once the container has built, you can start the application as written below.

### Start the application

First make sure that Docker Desktop is running, then run the following command in a terminal inside the directory *cv_matcher*.

```
docker run -it --rm -p 8501:8501 -p 8000:8000 -v "${PWD}:/workspaces/cvmatcher" -w /workspaces/cvmatcher -e PYTHONPATH=/workspaces/cvmatcher --name cvmatcher cvmatcher-dev
```

The API and Streamlit-App will start automatically, but note that there is some more wait time included in starting the API. After both applications have started successfully, the application can be accessed at http://localhost:8501/

Note that the matching won't work without any processed CVs.

### Process new CVs

Put example CVs in *input_cvs* and delete already parsed CVs from these directories if necessary.
<ul>
    <li>extracted_cvs</li>
    <li>extracted_cvs_matching</li>
</ul>

To process the CVs make sure the application has started, then run the following command
```
docker exec -it cvmatcher bash
```
Ensure you are in the docker container and the terminal looks something like this:
root@6c7b7f44dbc3:/workspaces/cvmatcher#

Then run the following command to process the CVs from the input folder

```
python src/extracting/extraction_main.py
```

The application is now good to go!

### Stop the application
To stop the application execute the following command or stop the container *cv_matcher* in Docker Desktop.
```
docker stop cvmatcher
```