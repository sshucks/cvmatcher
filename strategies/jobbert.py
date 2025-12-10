from definitions import *
from matching import JobBERTMatchingStep
from matching.bert.general_bert import EducationBertMatchingStep

class JobBERTMatchingCategories(MatchingStepCategories):
    
    category_args = {
        "education": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
    }

class GermanEduJobBERTMatchingCategories(MatchingStepCategories):

    category_args = {
        "education": {
            "weight": 1.0,
            "method": EducationBertMatchingStep(language="german"),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
    }

class EnglishEduJobBERTMatchingCategories(MatchingStepCategories):

    category_args = {
        "education": {
            "weight": 1.0,
            "method": EducationBertMatchingStep(language="english"),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
        "soft_skills": {
            "weight": 1.0,
            "method": JobBERTMatchingStep(),
        },
    }
