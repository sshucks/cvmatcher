import utils.esco_utils as e
import copy
from definitions import CVData, ProfessionalExperienceData, EducationData
from sentence_transformers import SentenceTransformer


class ESCOTranslateCV():
    """ Class to translate requirements to standardized ESCO terms """
    def __init__(self, args):
        """ 
        :param args: arguments for the class (mandatory: esco_language)
        :type args: Dict
        """
        self.model = SentenceTransformer("TechWolf/JobBERT-v3")
        self.language = args.get("esco_language")

        self.esco_skills = e.read_skills(self.language)
        self.esco_occupation = e.read_occupations(self.language)

        self.skill_preferredLabels = e.read_skill_preferredLabels(self.language)
        self.occupation_preferredLabels = e.read_occupation_preferredLabels(self.language)

    
    def run(self, cv: CVData, args) -> CVData:
        """ translate full CV
        
        :param cv: CV to be translated
        :type cv: CVData
        :param args: translation parameters (mandatory: esco_job_threshold, esco_education_threshold, esco_skill_threshold)
        :type args: Dict
        
        :return: translated CV
        :rtype: CVData
        """
        self.job_threshold = args.get("esco_job_threshold")
        self.education_threshold = args.get("esco_education_threshold")
        self.skill_threshold = args.get("esco_skill_threshold")


        cv["hard_skills"] = self.translate_skills(cv["hard_skills"], 3)
        cv["soft_skills"] = self.translate_skills(cv["soft_skills"], 3)
        cv["professional_experience"] = self.translate_prof_experience(cv["professional_experience"])
        cv["education"] = self.translate_education_via_jobs(cv["education"])

        return cv


    def translate_skills(self, skills:list[str], n:int = 1):
        """ translate skills to standardized ESCO terms

        :param skills: skills to be translated
        :type skills: list[str]
        :param n: max number of ESCO terms to be chosen per skill
        :type n: int

        :return: translated skills
        :rtype: list[str] 
        """
        esco_uris = e.ESCO_labelling(skills, self.esco_skills, self.model, self.skill_threshold, n, f"embeddings_skills_{self.language}.npy", self.language)
        esco_labels = e.get_skill_labels(esco_uris, self.skill_preferredLabels)
        return list(esco_labels)
    

    def translate_job_title(self, job_title:str):
        """ translate job title to standardized ESCO term

        :param job_title: job title to be translated
        :type job_title: str

        :return: translated job title
        :rtype: str
        """
        esco_uris = e.ESCO_labelling([job_title], self.esco_occupation, self.model, self.job_threshold, 1, f"embeddings_occupations_{self.language}.npy", self.language)
        esco_labels = e.get_job_labels(esco_uris, self.occupation_preferredLabels)

        if len(esco_labels) < 1:
            return job_title
        
        return list(esco_labels)[0]
    

    def translate_prof_experience(self, prof_experience: list[ProfessionalExperienceData]):
        """ translate experience to standardized ESCO terms

        :param prof_experience: experience to be translated
        :type prof_experience: list[ProfessionalExperienceData]

        :return: translated experience
        :rtype: list[ProfessionalExperienceData] 
        """
        translated = []

        for prof_ex in prof_experience:
            translated_prof = copy.deepcopy(prof_ex)
            translated_prof["job_title"] = self.translate_job_title(prof_ex["job_title"])
            translated_prof["responsibilities"] = list(self.translate_skills(prof_ex["responsibilities"], 3))

            translated.append(translated_prof)

        return translated

    def translate_education_via_jobs(self, education: list[EducationData]):
        """ translate education to standardized ESCO terms

        :param education: education to be translated
        :type education: list[EducationData]

        :return: translated education
        :rtype: list[EducationData] 
        """
        translated = []

        for ed in education:
            ed_copy = copy.deepcopy(ed)
            ed_copy["field_of_study"] = self.translate_job_title(ed["field_of_study"])

            translated.append(ed_copy)

        return translated
        


class ESCOEnrichCV(ESCOTranslateCV):
    """ Class to translate requirements to standardized ESCO terms and enrich with ESCO relationships """
    def __init__(self, args):
        """ 
        :param args: arguments for the class (mandatory: esco_language)
        :type args: Dict
        """

        super().__init__(args)
        self.skill_lookup = e.read_skill_hierarchy(self.language)
        self.skill_occ_relation = e.read_skill_occ_relation(self.language)

    def run(self, cv: CVData, args) -> CVData:
        """ translate and enrich full CV
        
        :param cv: CV to be translated
        :type cv: CVData
        :param args: translation parameters (mandatory: esco_job_threshold, esco_education_threshold, esco_skill_threshold)
        :type args: Dict
        
        :return: translated and enriched CV
        :rtype: CVData
        """
        self.job_threshold = args.get("esco_job_threshold")
        self.education_threshold = args.get("esco_education_threshold")
        self.skill_threshold = args.get("esco_skill_threshold")

        cv["professional_experience"] = super().translate_prof_experience(cv["professional_experience"])
        cv["education"] = super().translate_education_via_jobs(cv["education"])
        cv["hard_skills"] = self.translate_skills_with_hierarchy(cv["hard_skills"], 3)
        cv["hard_skills"] += self.enrich_hard_skills_with_exp(cv["professional_experience"])
        cv["hard_skills"] = list(set(cv["hard_skills"]))
        cv["soft_skills"] = self.translate_skills_with_hierarchy(cv["soft_skills"], 3)

        return cv

    
    def translate_skills_with_hierarchy(self, skills:list[str], n:int = 1):
        """ translate skills to standardized ESCO terms and enrich with broader hierarchical terms

        :param skills: skills to be translated
        :type skills: list[str]
        :param n: max number of ESCO terms to be chosen per skill
        :type n: int

        :return: translated and enriched skills
        :rtype: list[str] 
        """
        esco_uris = e.ESCO_labelling(skills, self.esco_skills, self.model, self.skill_threshold, n, f"embeddings_skills_{self.language}.npy", self.language)
        esco_enriched = e.enrich_ESCO(esco_uris, self.skill_lookup)
        esco_labels = e.get_skill_labels(esco_enriched, self.skill_preferredLabels)
        return list(esco_labels)
    

    def enrich_hard_skills_with_exp(self, prof_experience:list[ProfessionalExperienceData]):
        """ extract skills from professional experience and enrich with broader hierarchical terms

        :param prof_experience: professional experience of which skills should be extracted
        :type prof_experience: list[ProfessionalExperienceData]

        :return: extracted and enriched skills
        :rtype: list[str] 
        """
        profs = []
        resp = []

        for prof_exp in prof_experience:
            profs.append(prof_exp["job_title"])
            resp += prof_exp["responsibilities"]

        job_uris =  e.ESCO_labelling(profs, self.esco_occupation, self.model, self.job_threshold, 1, f"embeddings_occupations_{self.language}.npy", self.language)
        skill_uris = e.get_skills_for_occ(job_uris, self.skill_occ_relation)
        skill_uris = skill_uris | e.ESCO_labelling(resp, self.esco_skills, self.model, self.skill_threshold, 3, f"embeddings_skills_{self.language}.npy", self.language)

        skills_enriched = e.enrich_ESCO(skill_uris, self.skill_lookup)
        skills = e.get_skill_labels(skills_enriched, self.skill_preferredLabels)
        return list(skills)

