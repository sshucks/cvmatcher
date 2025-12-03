import os
from definitions import CategoryMatchingStep

PHP_SCRIPT_CV_EXTRACTION = "./src/extracting/cv/curlRequest.php"

# ------ INPUT / OUTPUT ------
CV_INPUT_DIR = "data/input_cvs"
CV_OUTPUT_DIR = "data/extracted_cvs"
CV_OUTPUT_DIR_MATCHING = "data/extracted_cvs_matching"
CV_STORAGE = "data/cv_database"

VALIDATION_DATA_DIR = "data/validation_data"

# ------ CACHING ------
DATABASE_FOLDER = "./caching"
DATABASE_FILE_NAME = "cv_caching.db"
DATABASE_FILE_PATH = os.path.join(DATABASE_FOLDER, DATABASE_FILE_NAME)
DATABASE_URL = f"sqlite:///{DATABASE_FILE_PATH}"

# ------ LLM PARSING ------
LLM_SYSTEM_PROMPT_PATH_CV_PARSING_DE= "./resources/llm/system_prompts/de/cv_parsing_instructions.md"
LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_DE = "./resources/llm/system_prompts/de/requirements_parsing_instructions.md"
LLM_SYSTEM_PROMPT_PATH_CV_PARSING_EN= "./resources/llm/system_prompts/en/cv_parsing_instructions.md"
LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_EN = "./resources/llm/system_prompts/en/requirements_parsing_instructions.md"
LLM_PARSED_CV_SCHEMA = "./resources/llm/schemas/cv_schema.json"
LLM_PARSED_REQUIREMENTS_SCHEMA = "./resources/llm/schemas/requirements_schema.json"
LLM_ENDPOINT = "http://host.docker.internal:11434/api/generate" #"http://localhost:11434/api/generate"
LLM_MODEL =  "llama3.1:8b"
LLM_RANDOM_SEED = 42
LLM_TEMPERATURE = 0.0
LLM_TOP_K  = 1
LLM_TOP_P = 1
LLM_MAJORITY_M = 2
LLM_MAJORITY_N = 3

# ------ MATCHING ------
DEFAULT_EDUCATION_MATCHING = CategoryMatchingStep()
DEFAULT_PROF_EXPIERENCE_MATCHING = CategoryMatchingStep()
DEFAULT_HARD_SKILLS_MATCHING = CategoryMatchingStep()
DEFAULT_SOFT_SKILL_MATCHING = CategoryMatchingStep()

DEFAULT_MATCHING_CONFIG  = {
             "education" : {
                "weight": 1,
                "method": DEFAULT_EDUCATION_MATCHING
             },
            "professional_experience" : {
                "weight": 1,
                "method": DEFAULT_PROF_EXPIERENCE_MATCHING
             },
            "hard_skills" : {
                "weight": 1,
                "method": DEFAULT_HARD_SKILLS_MATCHING
             },
            "soft_skills" : {
                "weight": 1,
                "method": DEFAULT_SOFT_SKILL_MATCHING
             },
             "m":LLM_MAJORITY_M,
             "n":LLM_MAJORITY_N
        }