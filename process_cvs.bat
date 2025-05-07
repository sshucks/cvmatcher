@echo off
setlocal

echo Checking for Python 3.12 installation...

:: Try to find Python 3.12 explicitly
for /f "delims=" %%i in ('where python 2^>nul') do (
    for /f "tokens=2 delims= " %%v in ('"%%i" --version 2^>^&1') do (
        echo Found: %%i - Version: %%v
        echo %%v | findstr /B "3.12" >nul
        if not errorlevel 1 (
            set PYTHON_PATH=%%i
            goto :venv_setup
        )
    )
)

:: If we reach here, Python 3.12 was not found
echo Python 3.12 not found. Downloading and installing...

:: Set installer variables
set PYTHON_INSTALLER=python-3.12.0-amd64.exe
set PYTHON_URL=https://www.python.org/ftp/python/3.12.0/%PYTHON_INSTALLER%

:: Download Python 3.12 installer
powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%PYTHON_URL%', '%PYTHON_INSTALLER%')"

:: Install Python 3.12 silently and add it to PATH
echo Installing Python 3.12...
start /wait %PYTHON_INSTALLER% /passive InstallAllUsers=1 PrependPath=1

:: Cleanup installer
del %PYTHON_INSTALLER%

:: Update PATH to recognize newly installed Python
set PYTHON_PATH=python
echo Python 3.12 installed successfully.

:: Proceed to virtual environment setup
:venv_setup
echo Setting up virtual environment...

:: Check if .venv already exists
if exist .venv (
    echo Virtual environment already exists. Activating...
) else (
    echo Creating a new virtual environment...
    %PYTHON_PATH% -m venv .venv
)

:: Activate the virtual environment
call .venv\Scripts\activate

:: Confirm activation
echo Virtual environment activated.

:: Install required dependencies (optional, modify as needed)
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt 2>nul || echo No requirements.txt found, skipping.

:: Run the Python script
echo ====================================
echo ====================================
echo Processing CVs
python code\extracting\extraction_main.py

:: Deactivate the virtual environment
deactivate

echo Script execution complete.
echo Press any key to exit.
pause