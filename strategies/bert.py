from definitions import *
from matching.bert import BertMatchingStep, EducationBertMatchingStep

class GermanBERTMatchingCategories(MatchingStepCategories):
    
    category_args = {
        "education": {
            "weight": 1.0,
            "method": EducationBertMatchingStep(language="german"),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": BertMatchingStep(language="german"),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": BertMatchingStep(language="german"),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": BertMatchingStep(language="german"),
        },
    }
    
    
class EnglishBERTMatchingCategories(MatchingStepCategories):
    
    category_args = {
        "education": {
            "weight": 1.0,
            "method": EducationBertMatchingStep(language="english"),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": BertMatchingStep(language="english"),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": BertMatchingStep(language="english"),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": BertMatchingStep(language="english"),
        },
    }
    
