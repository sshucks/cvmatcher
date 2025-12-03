from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers.util import cos_sim
import warnings

from definitions import EducationData
from matching.bert.bert import ABCBertMatchingStep, ABCExperienceBertMatchingStep

class BertMatchingStep(ABCBertMatchingStep):
    """
    General BERT Matching Step
    """
    def __init__(self, language):
        """
        Initialize the BertMatchingStep with the specified language model.
        
        :param self: Description
        :param language: Description
        """
        
        if language == "german":
            self.model_name = "google-bert/bert-base-german-cased"
        else:
            self.model_name = "google-bert/bert-base-uncased"
            
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        
        
    def embed_batch(self, texts: list[str], model, tokenizer):
        """
        Embed a batch of texts using the provided model and tokenizer.        
        :param self:
        :param texts: list of texts to embed
        :type texts: list[str]
        :param model: Model to use for embedding
        :param tokenizer: Tokenizer to use for embedding
        """
        inputs = tokenizer(texts, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            
        embeddings = outputs.last_hidden_state[:, 0, :]
        return embeddings


class EducationBertMatchingStep(BertMatchingStep):
    
    def __init__(self, language):
        super().__init__(language)

    def run(self, cv_data:list[EducationData], requirements: list[EducationData], args):
        """
        Method to run BERT matching on education data.
        
        :param self:
        :param cv_data: List of CV education entries
        :type cv_data: list[EducationData]
        :param requirements: List of requirement education entries
        :type requirements: list[EducationData]
        :param args: Additional arguments e.g. graduation penalty
        :type args: dict
        """
        
        # extract relevant fields
        cv_study = [cv["field_of_study"] for cv in cv_data]
        req_study = [req["field_of_study"] for req in requirements]
        
        cv_grad = [cv["graduated"] for cv in cv_data]
        
        penalty = args.get("graduation_penalty", 0.5)
        
        if cv_study and req_study:
            
            # embed and compute similarity
            req_emb = self.embed_batch(req_study, self.model, self.tokenizer)
            cv_emb = self.embed_batch(cv_study, self.model, self.tokenizer)
            sim_matrix = cos_sim(cv_emb, req_emb) # cv is rows, req is columns

            if cv_grad:
                # Reduce similarity by half for non-graduated candidates
                for i in range(len(cv_grad)):
                    if not cv_grad[i]:
                        sim_matrix[i, :] *= penalty
                    
            # TODO: degree level matching - no priority for now
            
            avg_similarities = torch.max(sim_matrix, dim=0).values.mean().item()
            
        else:
            # warn if data is missing
            if not cv_study:
                warnings.warn("No education entries found in CV data.")
            if not req_study:
                warnings.warn("No education entries found in requirements.")
                
            avg_similarities = None

        return avg_similarities


class ExperienceBertMatchingStep(BertMatchingStep, ABCExperienceBertMatchingStep):
    
    def __init__(self, language):
        super().__init__(language)
    