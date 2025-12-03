import utils.esco_utils as e
from definitions import ProfessionalExperienceData, EducationData, MatchingStep, RequirementsData, CVData
from sentence_transformers import SentenceTransformer
import pandas as pd

class EscoMatchingStep(MatchingStep):
    def __init__(self, args):
        super().__init__()
        
        self.language = args.get("esco_language")

    def hierarchical_matching(self, requirements:set[str], cv_labels:set[str], lookup:pd.DataFrame, hierarchical_decay:float):
        """ Function to match requirements and cv_labels

        :param requirements: ESCO labels of requirements
        :type requirements: Set[str]
        :param cv_labels: ESCO labels of CV
        :type cv_labels: Set[str]
        :param lookup: relations table, columns: child, parent
        :type lookup: pd.DataFrame
        :param hierarchical_decay: Hyperparameter to model the score values of broader hierarchical matches
        :type hierarchical_decay: float

        :return: Value 0-1, how well are the requirements covered in the cv
        :rtype: float
        """
        print("Terms in CV:")
        print(self.label(cv_labels))
        print("\nTerms in Requirements:")
        print(self.label(requirements))
        print("\nMatches:")
        enriched_labels = e.enrich_ESCO(cv_labels, lookup)

        matches = []
        score = 0

        for r in requirements:
            done = False
            weight = 1
            term = r
            
            while not done:
                if term in enriched_labels:
                    print(f"{self.label([term])}:{weight}")
                    score += weight
                    done = True
                    matches.append(term)
                else:
                    weight = weight * hierarchical_decay
                    if term in lookup['child'].values:
                        term = lookup[lookup['child'] == term].iloc[0]["parent"]
                    else:
                        print(f"{self.label([term])}:miss")
                        done = True
        
        return(score/len(requirements), matches)


class EducationEscoMatchingStep(EscoMatchingStep):
    def __init__(self, args):
        super().__init__(args)

        self.occupations = e.read_occupations(self.language)
        self.lookup = e.read_occupation_hierarchy(self.language)

        self.occupation_preferredLabels = e.read_occupation_preferredLabels(self.language)

    def run(self, education_cv: EducationData, education_req: EducationData, args) -> float:
        decay = args.get("esco_job_decay")

        cv_labels = [ed["field_of_study"] for ed in education_cv]
        req_labels = [ed["field_of_study"] for ed in education_req]

        cv_uris = e.get_job_uris(set(cv_labels), self.occupation_preferredLabels)
        req_uris = e.get_job_uris(set(req_labels), self.occupation_preferredLabels)

        score, matches = super().hierarchical_matching(req_uris, cv_uris, self.lookup, decay)

        #print(e.get_job_labels(matches, self.occupation_preferredLabels))
        return score
    
    def label(self, uris):
        return e.get_job_labels(uris, self.occupation_preferredLabels)


class ExperienceEscoMatchingStep(EscoMatchingStep):
    def __init__(self, args):
        super().__init__(args)

        self.occupations = e.read_occupations(self.language)
        self.lookup = e.read_occupation_hierarchy(self.language)

        self.occupation_preferredLabels = e.read_occupation_preferredLabels(self.language)

    def run(self, experience_cv: ProfessionalExperienceData, experience_req: ProfessionalExperienceData, args) -> float:
        decay = args.get("esco_job_decay")

        cv_labels = [ex["job_title"] for ex in experience_cv]
        req_labels = [ex["job_title"] for ex in experience_req]

        cv_uris = e.get_job_uris(set(cv_labels), self.occupation_preferredLabels)
        req_uris = e.get_job_uris(set(req_labels), self.occupation_preferredLabels)

        score, matches = super().hierarchical_matching(req_uris, cv_uris, self.lookup, decay)

        #print(e.get_job_labels(matches, self.occupation_preferredLabels))
        return score
    
    def label(self, uris):
        return e.get_job_labels(uris, self.occupation_preferredLabels)
    

class SkillEscoMatchingStep(EscoMatchingStep):
    def __init__(self, args):
        super().__init__(args)

        self.skills = e.read_skills(self.language)
        self.lookup = e.read_skill_hierarchy(self.language)

        self.skill_preferredLabels = e.read_skill_preferredLabels(self.language)

    def run(self, skills_cv: list[str], skills_req: list[str], args) -> float:
        decay = args.get("esco_skill_decay")

        cv_uris = e.get_skill_uris(set(skills_cv), self.skill_preferredLabels)
        req_uris = e.get_skill_uris(set(skills_req), self.skill_preferredLabels)

        score, matches = super().hierarchical_matching(req_uris, cv_uris, self.lookup, decay)

        #print(e.get_skill_labels(matches,self.skill_preferredLabels))
        return score
    
    def label(self, uris):
        return e.get_skill_labels(uris, self.skill_preferredLabels)
