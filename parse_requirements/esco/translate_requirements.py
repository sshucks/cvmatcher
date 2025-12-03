import utils.esco_utils as e
import copy
from definitions import RequirementsData, ProfessionalExperienceData, EducationData
from sentence_transformers import SentenceTransformer

class ESCOTranslateRequirements():
    """ Class to translate requirements to standardized ESCO terms """

    def __init__(self, args):
        self.model = SentenceTransformer("TechWolf/JobBERT-v3")
        self.language = args.get("esco_language")

        self.esco_skills = e.read_skills(self.language)
        self.esco_occupation = e.read_occupations(self.language)

        self.skill_preferredLabels = e.read_skill_preferredLabels(self.language)
        self.occupation_preferredLabels = e.read_occupation_preferredLabels(self.language)


    def run(self, requirements: RequirementsData, args) -> RequirementsData:
        job_threshold = args.get("esco_job_threshold")
        education_threshold = args.get("esco_education_threshold")
        skill_threshold = args.get("esco_skill_threshold")

        requirements["hard_skills"] = self.translate_skills(requirements["hard_skills"], skill_threshold)
        requirements["soft_skills"] = self.translate_skills(requirements["soft_skills"], skill_threshold)
        requirements["job_title"] = self.translate_job_title(requirements["job_title"], job_threshold)
        requirements["professional_experience"] = self.translate_prof_experience(requirements["professional_experience"], job_threshold)
        requirements["education"] = self.translate_education_via_jobs(requirements["education"], education_threshold)

        return requirements


    def translate_skills(self, skills:list[str], label_threshold:float, n:int = 1):
        esco_uris = e.ESCO_labelling(skills, self.esco_skills, self.model, label_threshold, n, f"embeddings_skills_{self.language}.npy", self.language)
        esco_labels = e.get_skill_labels(esco_uris, self.skill_preferredLabels)
        return list(esco_labels)
    

    def translate_job_title(self, job_title:str, label_threshold:float):
        esco_uris = e.ESCO_labelling([job_title], self.esco_occupation, self.model, label_threshold, 1, f"embeddings_occupations_{self.language}.npy", self.language)
        esco_labels = e.get_job_labels(esco_uris, self.occupation_preferredLabels)

        if len(esco_labels) < 1:
            return job_title
        
        return list(esco_labels)[0]
    

    def translate_prof_experience(self, prof_experience: list[ProfessionalExperienceData], label_threshold:float):
        translated = []

        for prof_ex in prof_experience:
            translated_prof = copy.deepcopy(prof_ex)
            translated_prof["job_title"] = self.translate_job_title(prof_ex["job_title"], label_threshold)

            translated.append(translated_prof)

        return translated

    def translate_education_via_jobs(self, education: list[EducationData], label_threshold:float):
        translated = []

        for ed in education:
            ed_copy = copy.deepcopy(ed)
            ed_copy["field_of_study"] = self.translate_job_title(ed["field_of_study"], label_threshold)

            translated.append(ed_copy)

        return translated
        
