import utils.esco_utils as e
from definitions import ProfessionalExperienceData, MatchingStep
from sentence_transformers import SentenceTransformer
import pandas as pd
from matching.esco.matching import ExperienceEscoMatchingStep
from datetime import datetime

class ExperienceDurationEscoMatchingStep(ExperienceEscoMatchingStep):
    """ Class for matching Experience with ESCO, with weighting of duration """
    def __init__(self, args):
        """ 
        :param args: arguments for the class (mandatory: esco_language)
        :type args: Dict
        """
        super().__init__(args)

    def run(self, experience_cv: ProfessionalExperienceData, experience_req: ProfessionalExperienceData, args) -> float:
        """ Do experience matching of cv and requirement, with weighting of duration

        :param experience_cv: ProfessionalExperienceData of CV
        :type experience_cv: ProfessionalExperienceData
        :param experience_req: ProfessionalExperienceData of Requirements
        :type experience_req: ProfessionalExperienceData
        :param args: parameters for the matching (mandatory: esco_job_decay)
        :type args: Dict

        :return: Value 0-1, how well are the requirements covered in the cv
        :rtype: float
        """
        self.decay = args.get("esco_job_decay")

        job_durations_cv_list = [{"job":ex["job_title"], "duration":self.get_duration(ex)} for ex in experience_cv]
        self.job_durations_cv = pd.DataFrame(job_durations_cv_list)

        job_durations_req_list = [{"job":ex["job_title"], "duration":ex["duration"]} for ex in experience_req]
        self.job_durations_req = pd.DataFrame(job_durations_req_list)

        return self.hierarchical_matching_duration()

    def get_duration(self, experience: ProfessionalExperienceData):
        """ function to calculate job duration from start and end date 
        
        :param experience: experience data from cv (mandatory keys: "start" and "end")
        :type experience: ProfessionalExperienceData

        :return: duration in years
        :rtype: float
        """
        fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
        start_dt = datetime.strptime(experience["start"], fmt)
        end_dt = datetime.strptime(experience["end"], fmt)

        duration = end_dt - start_dt
        return float(duration.days) / 365.0

    def hierarchical_matching_duration(self):
        """ function that implements the matching logic for matching professional experience with duration

        :return: Value 0-1, how well are the requirements covered in the cv
        :rtype: float
        """
        self.job_durations_cv["job"] = self.job_durations_cv["job"].apply(self.translate_uri)
        self.job_durations_req["job"] = self.job_durations_req["job"].apply(self.translate_uri)

        self.job_durations_cv = self.job_durations_cv.dropna()
        self.job_durations_req = self.job_durations_req.dropna()

        self.enrich_cv()
        self.job_durations_cv = self.job_durations_cv.groupby(["job"])["duration"].sum().reset_index()

        print("\nCV:")
        print([super().label([j]) for j in self.job_durations_cv["job"]])

        print("\nRequirements:")
        print([super().label([j]) for j in self.job_durations_req["job"]])

        score = 0
        matches = []

        for row in self.job_durations_req.iterrows():
            scores = []
            weight = 1
            req = row[1]
            uri = req["job"]
            duration = req["duration"]
            done = False

            while not done:
                print(uri)
                if uri in self.job_durations_cv["job"]:
                    # match occured
                    print(f"{super().label([uri])}:{weight}")
                    # get duration
                    cv_duration = self.job_durations_cv[self.job_durations_cv["job"]==uri]["duration"].iloc[0]

                    duration_score = 1
                    if duration != 0:
                        duration_score = cv_duration/duration

                    scores.append(weight * duration_score)
                    matches.append(uri)
                else:
                    weight = weight * self.decay
                    if uri in self.lookup['child'].values:
                        uri = self.lookup[self.lookup['child'] == uri].iloc[0]["parent"]
                    else:
                        done = True

            if len(scores) > 0:
                score += max(scores)
            else:
                print(f"{super().label([uri])}:miss")

        if(len(self.job_durations_req)) < 1:
            return None, []
        return(score/len(self.job_durations_req), matches)
    

    def translate_uri(self, term: str):
        """ function to get URI for standardized ESCO label

        :param term: standardized ESCO label to be translated
        :type term: str

        :return: Value 0-1, how well are the requirements covered in the cv
        :rtype: float
        """
        uris = e.get_job_uris(set([term]), self.occupation_preferredLabels)  
        return next(iter(uris), None)
      

    def enrich_cv(self):
        df = self.job_durations_cv.copy()

        # new column for all enriched terms
        df["enriched"] = df["job"].apply(lambda job: e.enrich_ESCO(set([job]), self.lookup))

        # explode into multiple rows
        df = df.explode("enriched")

        df["job"] = df["enriched"]
        df = df.drop(columns=["enriched"])

        self.job_durations_cv = df
        
