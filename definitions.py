from abc import ABC, abstractmethod
from typing import TypedDict, cast
import datetime
import warnings


class EducationData(TypedDict):
    """
    Structure of education data
    """
    degree: str
    field_of_study: str
    graduated: bool


class PersonalData(TypedDict):
    """
    Structure of personal data
    """
    name: str
    email: str
    phone: str
    address: str
    date_of_birth: datetime.date


class ProfessionalExperienceData(TypedDict):
    """
    Structure of professional experience data
    """
    job_title: str
    industry: str
    duration: str
    responsibilities: list[str]


class CVData(TypedDict):
    """
    Structure of CV data
    """
    personal_info: PersonalData
    hard_skills: list[str]
    soft_skills: list[str]
    education: list[EducationData]
    professional_experience: list[ProfessionalExperienceData]


class RequirementsData(TypedDict):
    """
    Structure of Requirements data
    """
    job_title: list[str]
    hard_skills: list[str]
    soft_skills: list[str]
    education: list[EducationData]
    professional_experience: list[ProfessionalExperienceData]


# class PipelineStep(ABC):
#      @abstractmethod
#      def run(self, arg):
#          pass

class RequirementsParsingStep(ABC):
    """
     Abstract class for requirements parsing
    """
    @abstractmethod
    def run(self, requirements_path: str, args) -> RequirementsData:
        """
        Abstract method to parse requirements file
        
        :param self: 
        :param requirements_path: Path to requirements file
        :type requirements_path: str
        :param args: Additional arguments
        :return: Parsed requirements data
        :rtype: RequirementsData
        """
        pass


class CVParsingStep(ABC):
    """
     Abstract class for CV parsing
    """
    @abstractmethod
    def run(self, cv_path: str, args) -> CVData:
        """
        Abstract method to parse CV file
        
        :param self: 
        :param cv_path: Path to CV file
        :type cv_path: str
        :param args: Additional arguments
        :return: Parsed CV data
        :rtype: CVData
        """
        pass


class MatchingStep(ABC):
    """
     Abstract class for matching
    """
    @abstractmethod
    def run(self, cv_data: CVData, requirements: RequirementsData, args) -> float:
        """
        Abstract method to perform matching between CV data and requirements data
        
        :param self: Description
        :param cv_data: Description
        :type cv_data: CVData
        :param requirements: Description
        :type requirements: RequirementsData
        :param args: Description
        :return: Description
        :rtype: float
        """
        pass


class CategoryArgument(TypedDict):
    """
    Defines the structure of category arguments
    
    weight: Weight assigned to this category in overall matching
    method: Method used for matching this category
    """
    weight: float
    method: MatchingStep


class CategoryArguments(TypedDict):
    """
    Defines the structure of category arguments for all categories
    """
    education: CategoryArgument
    professional_experience: CategoryArgument
    hard_skills: CategoryArgument
    soft_skills: CategoryArgument


class MatchingStepCategories(MatchingStep):
    
    """
    A class to perform matching across multiple categories with weights.
    """
    
    category_args: CategoryArguments 

    
    def normalize(weights):
        """
        Normalize a dictionary of weights so that they sum to 1.
        
        :param weights: Dictionary of weights to normalize
        :type weights: dict
        :return: Normalized weights
        :rtype: dict
        """
        total_weight = sum(weights.values())
        return {k: v / total_weight for k, v in weights.items()}

    def normalize_weights(self):
        """
        Normalize the weights of category_args so that they sum to 1.
        
        :param self:
        """
        weights = {category: args['weight']
                   for category, args in self.category_args.items()}
        normalized = self.normalize(weights)
        for category in self.category_args:
            self.category_args[category]['weight'] = normalized[category]

    def update_weights(self, args):
        """
        Update the weights of category_args based on provided args.
        
        :param self: Description
        :param args: Description
        """
        for category in self.category_args:
            if category + "_weight" in args:
                self.category_args[category]['weight'] = args[category + "_weight"]

    def run(self, cv_data: CVData, requirements: RequirementsData, cat_args) -> tuple[float, dict]:
        """
        Perform matching across multiple categories and compute a final score.
        
        :param self:
        :param cv_data: Parsed CV data
        :type cv_data: CVData
        :param requirements: Parsed requirements data
        :type requirements: RequirementsData
        :param args: Arguments including optional weights for categories
            education_weight: Weight for education category
            professional_experience_weight: Weight for professional experience category
            hard_skills_weight: Weight for hard skills category
            soft_skills_weight: Weight for soft skills category
        :return: Final matching score and individual category scores
        :rtype: tuple[float, dict]
        """
        
        # Update weights based on args
        self.update_weights(cat_args)
        self.normalize_weights()

        # Perform matching for each category and collect scores
        scores = {}
        weighted_scores = {}
        weights = {}

        for category, cat_args in self.category_args.items():
            
            # parse category arguments (weight and method)
            cat_args = cast(CategoryArgument, cat_args)
            weight = cat_args["weight"]
            matching = cat_args["method"]

            # get cv and requirements section for the category
            cv_section = cv_data[category]
            requirements_section = requirements[category]

            # if both entries exist, perform matching
            if cv_section and requirements_section:
                weights[category] = weight

                score = matching.run(cv_section, requirements_section, cat_args)

                scores[category] = score

                if score is None:
                    weights[category] = 0

            # if one of them is empty, set weight for this category to 0 and issue warning
            else:
                weights[category] = 0
                if not cv_section:
                    warnings.warn(f"CV data for '{category}' is empty.")

                if not requirements_section:
                    warnings.warn(
                        f"Requirements data for '{category}' is empty.")

        # normalize weights again after removing empty sections
        normalized_weights = self.normalize(weights)

        # calculate weighted scores
        weighted_scores = {
            category: score * normalized_weights[category]
            for category, score in scores.items()
        }

        # calculate final score
        final_score = sum(weighted_scores.values())

        return final_score, scores


class CVMatchingPipeline:
    """
    A class to run the CV matching pipeline consisting of a requirements parsing step, a CV parsing step, and a matching step.
    """
    def __init__(self, RequirementsParsingStep: RequirementsParsingStep, CVParsingStep: CVParsingStep, MatchingStep: MatchingStep):
        self.RequirementsParsingStep = RequirementsParsingStep
        self.CVParsingStep = CVParsingStep
        self.MatchingStep = MatchingStep

    def run_single_cv(self, requirements_path, cv_path, args):
        """
        Run the CV matching pipeline for a single CV.
        
        :param self:
        :param requirements_path: Path to requirements file
        :param cv_path: Path to CV file
        :param args: Additional arguments
        """
        
        requirements = self.RequirementsParsingStep.run(
            requirements_path, args)
        cv_data = self.CVParsingStep.run(cv_path, args)
        score = self.MatchingStep.run(cv_data, requirements, args)
        return score

    def run_multiple_cvs(self, requirement_path, cv_paths, args=None):
        """
        Run the CV matching pipeline for multiple CVs against a single requirements file.
        Requirements parsing is executed only once, then each CV is processed in a loop.
        
        :param self:
        :param requirement_path: Path to requirements file
        :param cv_paths: List of paths to CV files
        :param args: Additional arguments
        """
        
        print("Processing CVs for requirement:", requirement_path)
        results = []
        requirements = self.RequirementsParsingStep.run(
            requirement_path, args=args)

        # Loop through each CV path and process
        for cv_path in cv_paths:

            print("Processing CV:", cv_path)

            try:
                cv_data = self.CVParsingStep.run(cv_path, args=args)
                score, scores_dict = self.MatchingStep.run(cv_data, requirements, args=args)

                results.append({
                    "cv_path": cv_path,
                    "score": score,
                    "scores_detail": scores_dict
                })
            except Exception as e:
                print(f"Error processing CV {cv_path}: {e}")
                results.append({
                    "cv_path": cv_path,
                    "score": None,
                    "scores_detail": None
                })

        return results