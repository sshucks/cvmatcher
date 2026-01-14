set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%\.."
docker build -f .devcontainer/Dockerfile -t cvmatcher-dev .
pause