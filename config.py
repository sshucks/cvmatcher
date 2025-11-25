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

LLM_SYSTEM_PROMPT_PATH_CV_PARSING_DE= "./llm/system_prompts/de/cv_parsing_instructions.md",
LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_DE = "./llm/system_prompts/de/requirements_parsing_instructions.md",
LLM_SYSTEM_PROMPT_PATH_CV_PARSING_EN= "./llm/system_prompts/en/cv_parsing_instructions.md",
LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_EN = "./llm/system_prompts/en/requirements_parsing_instructions.md",
LLM_PARSED_CV_SCHEMA = "./llm/schemas/cv_schema.json"
LLM_PARSED_REQUIREMENTS_SCHEMA = "./llm/schemas/requirements_schema.json.json"
LLM_ENDPOINT = "http://localhost:11434/api/generate"
LLM_MODEL =  "llama3.1:8b"
LLM_RANDOM_SEED = 42
LLM_TEMPERATURE = 0.0
LLM_TOP_K  = 1
LLM_TOP_P = 1