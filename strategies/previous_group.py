from definitions import *

from matching.previous_group.match_applicants import match_applicant
from parse_requirements.previous_group.extract_requirements import extract_requirement
from parse_cv.previous_group.process_cvs import process_cv
from parse_cv.previous_group.read_json import read_json


# class PreviousGroupCategoryMatching(CategoryMatchingStep):
#     def run(self, cv_data, requirements, args) -> float:
#         score = match_applicant(cv_data, requirements)
#         return score

# class PreviousGroupMatchingCategories(MatchingStepCategories):
    
#     category_args = {
#         "education": {
#             "weight": 1.0,
#             "method": PreviousGroupCategoryMatching(),
#         },
#         "professional_experience": {
#             "weight": 1.0,
#             "method": PreviousGroupCategoryMatching(),
#         },
#         "hard_skills": {
#             "weight": 1.0,
#             "method": PreviousGroupCategoryMatching(),
#         },
#         "soft_skills": {
#             "weight": 1.0,
#             "method": PreviousGroupCategoryMatching(),
#         },
#     }
    
class PreviousGroupMatching(MatchingStep):
    
    weights = {
        "education_weight": 1.0,
        "professional_experience_weight": 1.0,
        "hard_skills_weight": 1.0,
        "soft_skills_weight": 1.0,
    }
    
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        score = match_applicant(cv_data, requirements, 
                                self.weights["professional_experience_weight"],
                                self.weights["hard_skills_weight"],
                                self.weights["soft_skills_weight"],
                                self.weights["education_weight"])
        return score
    

class PreviousGroupRequirementsParsing(RequirementsParsingStep):
    def run(self, requirements_path: str, args) -> RequirementsData:
        return extract_requirement(requirements_path)
    
class PreviousGroupCVParsing(CVParsingStep):
    def run(self, cv_path: str, args) -> CVData:
        cv_data = process_cv(cv_path)
        cv_data = read_json(cv_data)
        return cv_data
    

previous_group_pipeline = CVMatchingPipeline(
    RequirementsParsingStep=PreviousGroupRequirementsParsing(),
    CVParsingStep=PreviousGroupCVParsing(),
    MatchingStep=PreviousGroupMatching()
)

# score = previous_group_pipeline.run("validation_data/11425/B-Stellenbeschreibung.docx", "validation_data/11425/ABS/B-14.pdf", args)

# print(f"Matching Score: {score}")
