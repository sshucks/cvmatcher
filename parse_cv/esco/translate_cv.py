import utils.esco_utils as e
import copy
from definitions import CVData, ProfessionalExperienceData, EducationData
from sentence_transformers import SentenceTransformer

class ESCOTranslateCV():
    """ Class to translate requirements to standardized ESCO terms """
    def run(self, cv: CVData, args) -> CVData:
        #model = SentenceTransformer("TechWolf/JobBERT-v3")
        model = args.get("esco_embeddings_model")

        label_threshold = args.get("esco_threshold")

        cv["hard_skills"] = self.translate_skills(cv["hard_skills"], model, label_threshold)
        cv["soft_skills"] = self.translate_skills(cv["soft_skills"], model, label_threshold)
        cv["professional_experience"] = self.translate_prof_experience(cv["professional_experience"], model, label_threshold)
        cv["education"] = self.translate_education_via_jobs(cv["education"], model, label_threshold)

        return cv


    def translate_skills(self, skills:list[str], model:SentenceTransformer, label_threshold:float, n:int = 1):
        esco_skills = e.read_skills()
        esco_uris = e.ESCO_labelling(skills, esco_skills, model, label_threshold, n, "embeddings_skills.npy")
        esco_labels = e.get_skill_labels(esco_uris)
        return list(esco_labels)
    

    def translate_job_title(self, job_title:str, model:SentenceTransformer, label_threshold:float, n:int = 1):
        esco_occupation = e.read_occupations()
        esco_uris = e.ESCO_labelling([job_title], esco_occupation, model, label_threshold, n, "embeddings_occupations.npy")
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
        


class ESCOEnrichCV(ESCOTranslateCV):
    """ Class to translate requirements to standardized ESCO terms and enrich with ESCO relationships """
    def run(self, cv: CVData, args) -> CVData:
        #model = SentenceTransformer("TechWolf/JobBERT-v3")
        model = args.get("esco_embeddings_model")

        label_threshold = args.get("esco_threshold")

        cv["professional_experience"] = super().translate_prof_experience(cv["professional_experience"], model, label_threshold)
        cv["education"] = super().translate_education_via_jobs(cv["education"], model, label_threshold)
        cv["hard_skills"] = self.translate_skills_with_hierarchy(cv["hard_skills"], model, label_threshold, 3)
        cv["hard_skills"] += self.enrich_hard_skills_with_exp(cv["professional_experience"], model, label_threshold)
        cv["soft_skills"] = self.translate_skills_with_hierarchy(cv["soft_skills"], model, label_threshold, 3)

        return cv

    
    def translate_skills_with_hierarchy(self, skills:list[str], model:SentenceTransformer, label_threshold:float, n:int = 1):
        esco_skills = e.read_skills()
        esco_uris = e.ESCO_labelling(skills, esco_skills, model, label_threshold, n, "embeddings_skills.npy")
        lookup = e.read_skill_hierarchy()
        esco_enriched = e.enrich_ESCO(esco_uris, lookup)
        esco_labels = e.get_skill_labels(esco_enriched)
        return list(esco_labels)
    

    def enrich_hard_skills_with_exp(self, prof_experience:list[ProfessionalExperienceData], model:SentenceTransformer, label_threshold:float):
        profs = []
        resp = []

        for prof_exp in prof_experience:
            profs.append(prof_exp["job_title"])
            resp += prof_exp["responsibilities"]

        esco_occupation = e.read_occupations()
        esco_skills = e.read_skills()
        job_uris =  e.ESCO_labelling(profs, esco_occupation, model, label_threshold, 1, "embeddings_occupations.npy")
        skill_uris = e.get_skills_for_occ(job_uris)
        skill_uris += e.ESCO_labelling(resp, esco_skills, model, label_threshold, 3, "embeddings_skills.npy")

        lookup = e.read_skill_hierarchy()
        skills_enriched = e.enrich_ESCO(skill_uris, lookup)
        skills = e.get_skill_labels(skills_enriched)
        return skills

