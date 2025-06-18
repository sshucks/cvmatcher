import os

PHP_SCRIPT_CV_EXTRACTION = "./src/extracting/cv/curlRequest.php"

CV_INPUT_DIR = "input_cvs"
CV_OUTPUT_DIR = "extracted_cvs"
CV_OUTPUT_DIR_MATCHING = "extracted_cvs_matching"
CV_STORAGE = "cv_database"

DATABASE_FOLDER = "src/caching"
DATABASE_FILE_NAME = "cv_caching.db"
DATABASE_FILE_PATH = os.path.join(DATABASE_FOLDER, DATABASE_FILE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH}"
