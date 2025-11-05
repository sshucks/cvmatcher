from definitions import *

from matching.previous_group.match_applicants import match_applicant
from parse_requirements.previous_group.extract_requirements import extract_requirement
from parse_cv.previous_group.process_cvs import process_cv
from parse_cv.previous_group.read_json import read_json

class PreviousGroupMatching(MatchingStep):
    
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        """Implement matching logic here
        Args:
            cv_data (CVData): Parsed CV data
            requirements (RequirementsData): Parsed requirements data
            args (dict): Additional arguments for matching
                exp_weight: weight of working experience
                pro_weight: weight of professional skills
                per_weight: weight of personal skills
                edu_weight: weight of education
        Returns:
            float: Matching score
        """

        experience_weight = args.get("experience_weight")
        professional_weight = args.get("professional_weight")
        personal_weight = args.get("personal_weight")
        education_weight = args.get("education_weight")

        return match_applicant(cv_data, requirements, experience_weight, professional_weight, personal_weight, education_weight)

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
