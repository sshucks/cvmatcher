import torch
import numpy as np
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import batch_to_device
from matching.bert.bert import ABCBertMatchingStep

class JobBERTMatchingStep(ABCBertMatchingStep):
    
    def __init__(self):
        self.model = SentenceTransformer("TechWolf/JobBERT-v3")
    
    def encode(self, jobbert_model, texts):
        """
        Encode texts using the JobBERT model.

        :param self:
        :param jobbert_model: model to use for encoding
        :param texts: list of texts to encode
        """
        
        features = jobbert_model.tokenize(texts)
        features = batch_to_device(features, jobbert_model.device)
        features["text_keys"] = ["anchor"]
        with torch.no_grad():
            out_features = jobbert_model.forward(features)
        return out_features["sentence_embedding"].cpu().numpy()
    
    def embed_batch(self, texts: list[str], model, batch_size):
        # Sort texts by length and keep track of original indices
        sorted_indices = np.argsort([len(text) for text in texts])
        sorted_texts = [texts[i] for i in sorted_indices]
        
        embeddings = []
        
        # Encode in batches
        for i in tqdm(range(0, len(sorted_texts), batch_size)):
            batch = sorted_texts[i:i+batch_size]
            embeddings.append(self.encode(model, batch))
        
        # Concatenate embeddings and reorder to original indices
        sorted_embeddings = np.concatenate(embeddings)
        original_order = np.argsort(sorted_indices)
        return sorted_embeddings[original_order]
