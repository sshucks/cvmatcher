import utils.esco_utils as e
import copy
from definitions import RequirementsData, ProfessionalExperienceData, EducationData
from sentence_transformers import SentenceTransformer

class ESCOTranslateRequirements():
    """ Class to translate requirements to standardized ESCO terms """
    def run(self, requirements: RequirementsData, args) -> RequirementsData:
        #model = SentenceTransformer("TechWolf/JobBERT-v3")
        model = args.get("esco_embeddings_model")

        label_threshold = args.get("esco_threshold")

        requirements["hard_skills"] = self.translate_skills(requirements["hard_skills"], model, label_threshold)
        requirements["soft_skills"] = self.translate_skills(requirements["soft_skills"], model, label_threshold)
        requirements["job_title"] = self.translate_job_title(requirements["job_title"], model, label_threshold)
        requirements["professional_experience"] = self.translate_prof_experience(requirements["professional_experience"], model, label_threshold)
        requirements["education"] = self.translate_education_via_jobs(requirements["education"], model, label_threshold)

        return requirements


    def translate_skills(self, skills:list[str], model:SentenceTransformer, label_threshold:float, n:int = 1):
        esco_skills = e.read_skills()
        esco_uris = e.ESCO_labelling(skills, esco_skills, model, label_threshold, n, "embeddings_skills.npy")
        esco_labels = e.get_skill_labels(esco_uris)
        return list(esco_labels)
    

    def translate_job_title(self, job_title:str, model:SentenceTransformer, label_threshold:float):
        esco_occupation = e.read_occupations()
        esco_uris = e.ESCO_labelling([job_title], esco_occupation, model, label_threshold, 1, "embeddings_occupations.npy")
        esco_labels = e.get_job_labels(esco_uris)

        if len(esco_labels) < 1:
            return job_title
        
        return list(esco_labels)[0]
    

    def translate_prof_experience(self, prof_experience: list[ProfessionalExperienceData],model:SentenceTransformer, label_threshold:float):
        translated = []

        for prof_ex in prof_experience:
            translated_prof = copy.deepcopy(prof_ex)
            translated_prof["job_title"] = self.translate_job_title(prof_ex["job_title"], model, label_threshold)

            translated.append(translated_prof)

        return translated

    def translate_education_via_jobs(self, education: list[EducationData],model:SentenceTransformer, label_threshold:float):
        translated = []

        for ed in education:
            ed_copy = copy.deepcopy(ed)
            ed_copy["field_of_study"] = self.translate_job_title(ed["field_of_study"], model, label_threshold)

            translated.append(ed_copy)

        return translated
        
