from abc import abstractmethod
from sentence_transformers.util import cos_sim
import torch
import numpy as np
import warnings

from definitions import MatchingStep, ProfessionalExperienceData


class ABCBertMatchingStep(MatchingStep):
    """
    Abstract BERT Matching Step
    """
    
    def run(self, requirements: list[str], cv_positions: list[str], tokenizer, model):
        """
        Perform BERT-based matching between requirements and CV positions.
        
        :param self: 
        :param requirements: List of requirement strings
        :type requirements: list[str]
        :param cv_positions: List of CV strings
        :type cv_positions: list[str]
        :param tokenizer: Tokenizer to use for embedding
        :param model: Model to use for embedding
        """
        
        # embed requirements and CV positions
        req_emb = self.embed_batch(requirements, tokenizer, model)
        cv_emb = self.embed_batch(cv_positions, tokenizer, model)
        
        # compute cosine similarity matrix
        sim_matrix = cos_sim(cv_emb, req_emb)

        # get the maximum similarity score for each requirement and compute mean across all requirements
        sim_score = torch.max(sim_matrix, dim=0).values.mean().item()
        return sim_score
    
    @abstractmethod
    def embed_batch(self, texts: list[str], model, tokenizer = None, batch_size=8):
        """
        Embed a batch of texts using the provided model and tokenizer.
        
        :param self: 
        :param texts: list of texts to embed
        :type texts: list[str]
        :param model: Model to use for embedding
        :param tokenizer: Tokenizer to use for embedding
        :param batch_size: Batch size
        :type batch_size: int
        """
        
        return
    
    
class ABCExperienceBertMatchingStep(ABCBertMatchingStep):

    def run(self, cv_data:list[ProfessionalExperienceData], requirements: ProfessionalExperienceData, args):
        """
        Method to run BERT matching on professional experience data.
        
        :param self: 
        :param cv_data: List of professional experience data from CV
        :type cv_data: list[ProfessionalExperienceData]
        :param requirements: list of professional experience data from requirements
        :type requirements: ProfessionalExperienceData
        :param args: Additional arguments
        """
        
        # extract relevant fields
        cv_positions = [cv["job_title"] for cv in cv_data]
        req_positions = [requirements["job_title"]]
        
        cv_industries = [cv["industry"] for cv in cv_data]
        req_industries = [requirements["industry"]]
        
        
        if cv_positions and req_positions:
            title_score = self.run(req_positions, cv_positions, self.tokenizer, self.model)
        else:
            # if one of the lists is empty, we cannot compute a score
            title_score = None
            
            if not cv_positions:
                warnings.warn("No job titles found in CV data.")
            if not req_positions:
                warnings.warn("No job titles found in requirements.")
                
                
        if cv_industries and req_industries:
            industry_score = self.run(req_industries, cv_industries, self.tokenizer, self.model)
        else:
            # if one of the lists is empty, we cannot compute a score
            industry_score = None
            
            if not cv_industries:
                warnings.warn("No industries found in CV data.")
            if not req_industries:
                warnings.warn("No industries found in requirements.")

        # TODO weight results by duration and check order of embedding results
        # req_duration = [requirements["duration"]]
        # cv_duration = [cv["duration"] for cv in cv_data]
        
        # compute average similarity, ignoring None values (if matching could not be performed due to missing data)
        scores = [score for score in [title_score, industry_score] if score is not None]
        if scores:
            average_similarity = np.mean(scores)
        else:
            average_similarity = None

        return average_similarity
    