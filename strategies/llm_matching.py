from definitions import *
from matching.llm.matching_llm import LLMPartlyMatchingStep
from config import LLM_MATCHING_SCHEMA, LLM_SYSTEM_PROMPT_PATH_MATCHING_DE



class LLMPartlyMatching(MatchingStepCategories):

    category_args = {
        "education": {
            "weight": 1.0,
            "method": LLMPartlyMatchingStep(system_prompt_path=LLM_SYSTEM_PROMPT_PATH_MATCHING_DE, 
                                            response_schema_path=LLM_MATCHING_SCHEMA),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": LLMPartlyMatchingStep(system_prompt_path=LLM_SYSTEM_PROMPT_PATH_MATCHING_DE, 
                                            response_schema_path=LLM_MATCHING_SCHEMA),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": LLMPartlyMatchingStep(system_prompt_path=LLM_SYSTEM_PROMPT_PATH_MATCHING_DE, 
                                            response_schema_path=LLM_MATCHING_SCHEMA),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": LLMPartlyMatchingStep(system_prompt_path=LLM_SYSTEM_PROMPT_PATH_MATCHING_DE, 
                                            response_schema_path=LLM_MATCHING_SCHEMA),
        },
    }

