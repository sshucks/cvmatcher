from definitions import MatchingStepCategories
from matching.bert.jobbert import JobBERTMatchingStep
from matching.bert.bert import ExperienceBertMatchingStep
from matching.bert.general_bert import EducationBertMatchingStep

# class JobBERTMatchingCategories(MatchingStepCategories):
    
#     category_args = {
#         "education": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#         "professional_experience": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#         "hard_skills": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#         "soft_skills": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#     }

jobbert = JobBERTMatchingStep()

class GermanEduJobBERTMatchingCategories(MatchingStepCategories):

    category_args = {
        "education": {
            "weight": 1.0,
            "method": EducationBertMatchingStep(language="german"),
        },
        "professional_experience": {
            "weight": 1.0,
            "method": ExperienceBertMatchingStep(jobbert),
        },
        "hard_skills": {
            "weight": 1.0,
            "method": jobbert,
        },
        "soft_skills": {
            "weight": 1.0,
            "method": jobbert,
        },
    }

# class EnglishEduJobBERTMatchingCategories(MatchingStepCategories):

#     category_args = {
#         "education": {
#             "weight": 1.0,
#             "method": EducationBertMatchingStep(language="english"),
#         },
#         "professional_experience": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#         "hard_skills": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#         "soft_skills": {
#             "weight": 1.0,
#             "method": JobBERTMatchingStep(),
#         },
#     }
