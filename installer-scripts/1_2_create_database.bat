@echo off

set CONTAINER_NAME=cvmatcher
set IMAGE_NAME=cvmatcher-dev

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."

REM Check if container exists
docker ps -a --filter "name=%CONTAINER_NAME%" --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul
if %ERRORLEVEL%==0 (
        docker start %CONTAINER_NAME%
) else (
    echo Creating and running new container %CONTAINER_NAME%...
    docker run -dit -p 8501:8501 -p 8000:8000 -v "%cd%:/workspaces/cvmatcher" -w /workspaces/cvmatcher -e PYTHONPATH=/workspaces/cvmatcher --name %CONTAINER_NAME% %IMAGE_NAME% bash
)

docker exec -it %CONTAINER_NAME% python caching/database.py

pause