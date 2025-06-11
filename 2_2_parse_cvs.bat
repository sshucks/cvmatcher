@echo off

set CONTAINER_NAME=cvmatcher

docker ps --filter "name=%CONTAINER_NAME%" --filter "status=running" --format "{{.Names}}" | findstr /i "%CONTAINER_NAME%" >nul

if %ERRORLEVEL%==0 (
    echo Container %CONTAINER_NAME% is already running.
) else (
    echo Container %CONTAINER_NAME% is not running. Starting it...
    docker start %CONTAINER_NAME%
)

docker exec -it %CONTAINER_NAME% python src/extracting/extraction_main.py

pause