# SPD2_TRESCON: CV_Matcher

This projects aims to match the best applicants to a job description based on their CV.

## Setup

### Requirements
Download and Install Docker Desktop: https://docs.docker.com/get-started/introduction/get-docker-desktop/

### Get Source Code
Either clone the repository like this
```
git clone https://github.com/sshucks/cvmatcher
cd cvmatcher
```
or unzip the downloaded source code in your desired workspace.

### 1. Installation
Make sure that Docker Desktop is running, then execute *1_installer.bat*
This can take quite a long time (up to 20 minutes). Once the container has built, you can execute 1_2_create_database. These steps only need to be executed once.
After that you can start the application as written below.

### 2. Run application
Run *2_start_application* to create and run the Docker container.

### 3. Stop application
To stop the application run *3_stop_application.bat*

## Docker Commands to start application without VSCode and Batch Files

### Build Docker Container
Make sure that Docker Desktop is running, then open a terminal in the directory *cv_matcher* and run the following command to build the docker container. 

```
docker build -f .devcontainer/Dockerfile -t cvmatcher-dev .
```

This can take quite a long time (up to 20 minutes) and only needs to be done once. Once the container has built, you can create the database and start the application as written below.

### Start application

First make sure that Docker Desktop is running, then run the following command in a terminal inside the directory *cv_matcher*.

If you are using Windows:
```
docker run -it --rm -p 8501:8501 -p 8000:8000 -v "%cd%:/workspaces/cvmatcher" -w /workspaces/cvmatcher -e PYTHONPATH=/workspaces/cvmatcher --name cvmatcher cvmatcher-dev
```

If you are using Linux or WSL:
```
docker run -it --rm -p 8501:8501 -p 8000:8000 -v "${PWD}:/workspaces/cvmatcher" -w /workspaces/cvmatcher -e PYTHONPATH=/workspaces/cvmatcher --name cvmatcher cvmatcher-dev
```

Then execute this command to start a bash in the Docker-Container.
```
docker exec -it cvmatcher bash
```

### Create Database
If you haven't created the database yet, execute this command (only needs to be done once)
```
python caching/database.py
```

### Start FastAPI
```
python -m fastapi dev application/api_call.py
```

### Start Streamlit App
```
python -m streamlit run application/api_call.py
```

Note that there is some more wait time included in starting the API. 
After both applications have started successfully, the application can be accessed at http://localhost:8501/


### Stop the application
To stop the application execute the following command or stop the container *cv_matcher* in Docker Desktop.
```
docker stop cvmatcher
```

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

Start the API and Streamlit-App using the commands. Note that there is some more wait time included in starting the API. After both applications have started successfully, the application can be accessed at http://localhost:8501/

#### Create Databse
The database has to be created once.
```
python caching/database.py
```

#### Start FastAPI
```
python -m fastapi dev application/api_call.py
python -m fastapi dev application/api_call.py
```

#### Start Streamlit App
```
python -m streamlit run application/matching_app.py
```

