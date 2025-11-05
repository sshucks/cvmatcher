import os

PHP_SCRIPT_CV_EXTRACTION = "./src/extracting/cv/curlRequest.php"

CV_INPUT_DIR = "data/input_cvs"
CV_OUTPUT_DIR = "data/extracted_cvs"
CV_OUTPUT_DIR_MATCHING = "data/extracted_cvs_matching"
CV_STORAGE = "data/cv_database"

VALIDATION_DATA_DIR = "data/validation_data"

DATABASE_FOLDER = "src/caching"
DATABASE_FILE_NAME = "cv_caching.db"
DATABASE_FILE_PATH = os.path.join(DATABASE_FOLDER, DATABASE_FILE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH}"
