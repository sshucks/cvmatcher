from abc import ABC, abstractmethod

from typing import TypedDict, cast, List, Dict
import datetime
import os
import json

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
    hard_skills: list[str]
    soft_skills: list[str]
    education: list[EducationData]
    professional_experience: list[ProfessionalExperienceData]

class RequirementsData(TypedDict):
    job_title: str
    hard_skills: list[str]
    soft_skills: list[str]
    education: EducationData
    professional_experience: ProfessionalExperienceData
    

# class PipelineStep(ABC):
#      @abstractmethod
#      def run(self, arg):
#          pass
     
class RequirementsParsingStep():
     @abstractmethod
     def run(self, requirements_path: str, args) -> RequirementsData:
        pass
     
class CVParsingStep():
    @abstractmethod
    def run(self, cv_path: str, args) -> CVData:
       pass
   
class CategoryMatchingStep():
    @abstractmethod
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        pass
    
class CategoryArgument(TypedDict):
    weight: float
    method: CategoryMatchingStep
    
class CategoryArguments(TypedDict):
    education : CategoryArgument
    professional_experience : CategoryArgument
    hard_skills : CategoryArgument
    soft_skills : CategoryArgument

class MatchingStep():
    @abstractmethod
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        pass
    
    
class MatchingStepCategories():
    category_args: CategoryArguments
    
    def normalize_weights(self):
        total_weight = sum(cast(CategoryArgument, arg)["weight"] for arg in self.category_args.values())        
        for category in self.category_args:
            self.category_args[category]['weight'] /= total_weight
            
    def update_weights(self, args):
        for category in self.category_args:
            if category + "_weight" in args:
                self.category_args[category]['weight'] = args[category + "_weight"]
        
    
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> tuple[float, dict]:
        self.update_weights(args)
        self.normalize_weights()
        
        scores = {}
        weighted_scores = {}

        for category, args in self.category_args.items():
            args = cast(CategoryArgument, args)
            
            weight = args["weight"]
            matching = args["method"]
            
            cv_section = cv_data[category]
            requirements_section = requirements[category]
            
            score = matching.run(cv_section, requirements_section, args)

            scores[category] = score
            weighted_scores[category] = score * weight
        
        final_score = sum(weighted_scores.values())

        return final_score, scores


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
    
    def run_multiple_cvs(self, requirement_path, cv_paths:Dict[str, List[str]], args=None):
        results = []
        requirements = self.RequirementsParsingStep.run(requirement_path, args=args)
        cv_paths_more = [(item, key) for key, values in cv_paths.items() for item in values]
        print("Processing CVs for requirement:", requirement_path)
        for cv_path in cv_paths_more:
            print("Processing CV:", cv_path)
            
            try: 
                if cv_path[1] == "raw":
                    print("parsing cv")
                    cv_data = self.CVParsingStep.run(cv_path[0], args=args)
                elif cv_path[1] == "parsed":
                    print("reading already parsed cv from file system")
                    with open(cv_path[0]) as parsed_cv:
                        cv_data = json.loads(parsed_cv)

                score = 0#self.MatchingStep.run(cv_data, requirements, args=args)
            
                results.append({
                    "cv_path": cv_path,
                    "score": score
                })
            except Exception as e:
                print(f"Error processing CV {cv_path}: {repr(e)}")
                results.append({
                    "cv_path": cv_path,
                    "score": None
                })

        return results

