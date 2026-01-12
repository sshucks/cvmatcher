import os, json
import subprocess
import tempfile
import pandas as pd
import fitz
import pymupdf


async def convert_docx_to_pdf(file_path, new_name:str, output_dir:str):
    """Convert a docx file into a pdf using libreoffice and store with altered name

    :param file: docx file to convert
    :type file: UploadFile
    :param new_name: new name of the file
    :type new_name: str
    :param output_dir: location to store the converted file
    :type output_dir: str
    """

    # open file
    with open(file_path, "rb") as file:
    
        # parse the extension from input file for dynamic conversion
        input_extension = file_path.filename.split(".")[-1]
        
        # store data in temporary file
        temp_input_file = None
        
        # try to convert
        try:
            
            # convert provided file into a temporary file
            temp_input_file = tempfile.NamedTemporaryFile(suffix=f".{input_extension}", delete=False)
            temp_input_file.write(await file.read())
            temp_input_file.close()

            # ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # define LibreOffice coammand to convert the temporary file
            command = [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                temp_input_file.name # pass the path of the temporary input file
            ]

            # use check=True to raise an exception if LibreOffice returns a non-zero exit code
            result = subprocess.run(command, capture_output=True, check=True)
            
            # parse the path of the converted file
            temp_base_name = os.path.basename(os.path.splitext(temp_input_file.name)[0])
            default_output_filename = f"{temp_base_name}.pdf"
            actual_libreoffice_output_path = os.path.join(output_dir, default_output_filename)

            # rename the converted file
            desired_file_path = actual_libreoffice_output_path.replace(temp_base_name, new_name)
            os.rename(actual_libreoffice_output_path, desired_file_path)
            
            if result.stderr:
                print(f"LibreOffice stderr: {result.stderr.decode()}")
            if result.stdout:
                print(f"LibreOffice stdout: {result.stdout.decode()}")

            print(f"File converted. Check '{output_dir}' for the PDF.")

        except subprocess.CalledProcessError as e:
            print(f"LibreOffice conversion failed: {e}")
            print(f"stdout: {e.stdout.decode()}")
            print(f"stderr: {e.stderr.decode()}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # clean up the temporary input file
            if temp_input_file and os.path.exists(temp_input_file.name):
                
                # delete the temporary file
                os.unlink(temp_input_file.name)

def read_pdf(file_path:str) ->str:
    text = ""
    with pymupdf.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def make_history_file_if_not_exists():
    """Create the matching history file if it does not exist
    """
    from config import MATCHING_HISTORY_PATH

    if not os.path.exists(MATCHING_HISTORY_PATH):
        with open(MATCHING_HISTORY_PATH, "w") as history_file:
            json.dump([], history_file, indent=4)

def update_history(requirements_file:str, cout_cvs:int, accepted:int, rejected:int):
    """Update the matching history file with a new entry
    :param requirements_file: name of the requirements file used
    :type requirements_file: str
    :param cout_cvs: number of CVs processed
    :type cout_cvs: int
    :param accepted: number of accepted CVs
    :type accepted: int
    :param rejected: number of rejected CVs
    :type rejected: int
    """
    from config import MATCHING_HISTORY_PATH
    
    make_history_file_if_not_exists()
    
    with open(MATCHING_HISTORY_PATH, "r") as history_file:
        history_file.seek(0)
        try:
            history = json.load(history_file)
        except json.JSONDecodeError:
            history = []
        
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_entry = {
        "time": now,
        "requirements_file": requirements_file,
        "num_cvs": cout_cvs,
        "accepted": accepted,
        "rejected": rejected
    }
        
    history.append(new_entry)
    
    with open(MATCHING_HISTORY_PATH, "r+") as history_file:
        json.dump(history, history_file, indent=4)
        

def load_application_settings() -> dict:
    """Load application settings from a JSON file
    :param settings_path: path to the settings file
    :type settings_path: str
    :return: settings as a dictionary
    :rtype: dict
    """
    from config import APPLICATION_SETTINGS_PATH

    with open(APPLICATION_SETTINGS_PATH, "r", encoding='utf-8') as settings_file:
        settings = json.load(settings_file)
    return settings
