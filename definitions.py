from abc import ABC, abstractmethod

from typing import TypedDict
import datetime
import pandas as pd


class EducationData(TypedDict):
    degree: str
    field_of_study: str

class PersonalData(TypedDict):
    name: str
    email: str
    phone: str
    address: str
    date_of_birth: datetime.date

class ProfessionalExperienceData(TypedDict):
    job_title: str
    industry: str
    duration: str
    responsibilities: list[str]

class CVData(TypedDict):
    personal_info: PersonalData
    industry_skills: list[str]
    non_industry_skills: list[str]
    education: list[EducationData]
    professional_experience: list[ProfessionalExperienceData]

class RequirementsData(TypedDict):
    job_title: str
    industry_skills: list[str]
    non_industry_skills: list[str]
    education: EducationData
    professional_experience: ProfessionalExperienceData

class PipelineStep(ABC):
     @abstractmethod
     def run(self, arg):
         pass
     
class RequirementsParsingStep(PipelineStep):
     @abstractmethod
     def run(self, requirements_path: str, args) -> RequirementsData:
        pass
     
class CVParsingStep(PipelineStep):
    @abstractmethod
    def run(self, cv_path: str, args) -> CVData:
       pass
     
class MatchingStep(PipelineStep):
    @abstractmethod
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        pass

class CVMatchingPipeline:
    def __init__(self, RequirementsParsingStep: RequirementsParsingStep, CVParsingStep: CVParsingStep, MatchingStep: MatchingStep):
        self.RequirementsParsingStep = RequirementsParsingStep
        self.CVParsingStep = CVParsingStep
        self.MatchingStep = MatchingStep

    def run_single_cv(self, requirements_path, cv_path, args):
        requirements = self.RequirementsParsingStep.run(requirements_path, args)
        cv_data = self.CVParsingStep.run(cv_path, args)
        score = self.MatchingStep.run(cv_data, requirements, args)
        return score
    
    def run_multiple_cvs(self, requirement_path, cv_paths, args):
        print("Processing CVs for requirement:", requirement_path)
        results = []
        requirements = self.RequirementsParsingStep.run(requirement_path, args=args)

        for cv_path in cv_paths:
            
            print("Processing CV:", cv_path)
            
            cv_data = self.CVParsingStep.run(cv_path, args=args)
            score = self.MatchingStep.run(cv_data, requirements, args=args)
        
            results.append({
                "cv_path": cv_path,
                "score": score
            })

        return results

