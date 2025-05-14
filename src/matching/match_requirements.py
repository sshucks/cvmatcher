import torch
import os
import json
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel

class Model:
    def __init__(self, model_name: str):
        self.model = self._get_model(model_name)
        self.tokenizer = self._get_tokenizer(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

    def _get_model(self, model_name: str):
        return AutoModel.from_pretrained(model_name)    
    
    def _get_tokenizer(self, model_name: str):
        return AutoTokenizer.from_pretrained(model_name)
    
    def _get_embeddings(self, texts: list):
        encoded_inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        input_ids = encoded_inputs["input_ids"].to(self.device)
        attention_mask = encoded_inputs["attention_mask"].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
        
        cls_embeddings = outputs.last_hidden_state[:, 0, :]
        return cls_embeddings
    
    def _calculate_similarity(self, requirement_embeddings: torch.Tensor, skill_embeddings: torch.Tensor):
        return cosine_similarity(requirement_embeddings, skill_embeddings)
    
    def _get_score_for_best_matches(self, similarity_matrix, requirement_list, skill_list):
        result_dict = {}
        for i, term in enumerate(requirement_list):
            similarities = similarity_matrix[i]
            best_match_idx = similarities.argmax()
            best_match_term = skill_list[best_match_idx.item()]
            best_score = similarities[best_match_idx.item()]
            result_dict[term] = {"Match": best_match_term,
                                 "Score": best_score}
            
        return result_dict
    
    def get_requirements_embeddings(self, requirements):
        return self._get_embeddings(requirements)
    
    def get_cv_embeddings(self, skills):
        return self._get_embeddings(skills)
    
    def calculate_match(self, requirement_embeddings: torch.Tensor, skill_embeddings: torch.Tensor, requirement_list: list, skill_list: list):
        similarity_matrix = self._calculate_similarity(requirement_embeddings, skill_embeddings)
        result_dict = self._get_score_for_best_matches(similarity_matrix, requirement_list, skill_list)
        return result_dict

