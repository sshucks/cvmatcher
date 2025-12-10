import torch
import numpy as np
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import batch_to_device, cos_sim

import pytesseract
from pdf2image import convert_from_path

def convert_pdf_to_text(pdf_path):
    pages = convert_from_path(pdf_path)

    text_content = ""

    for page in pages:
        text = pytesseract.image_to_string(page, lang="deu+eng")
        text_content += text + "\n"

    return text_content

# Load the model
model = SentenceTransformer("TechWolf/JobBERT-v3")

def encode_batch(jobbert_model, texts):
    features = jobbert_model.tokenize(texts)
    features = batch_to_device(features, jobbert_model.device)
    features["text_keys"] = ["anchor"]
    with torch.no_grad():
        out_features = jobbert_model.forward(features)
    return out_features["sentence_embedding"].cpu().numpy()

def encode(jobbert_model, texts, batch_size: int = 8):
    # Sort texts by length and keep track of original indices
    sorted_indices = np.argsort([len(text) for text in texts])
    sorted_texts = [texts[i] for i in sorted_indices]
    
    embeddings = []
    
    # Encode in batches
    for i in tqdm(range(0, len(sorted_texts), batch_size)):
        batch = sorted_texts[i:i+batch_size]
        embeddings.append(encode_batch(jobbert_model, batch))
    
    # Concatenate embeddings and reorder to original indices
    sorted_embeddings = np.concatenate(embeddings)
    original_order = np.argsort(sorted_indices)
    return sorted_embeddings[original_order]

# Example usage
# job_titles = [
#     'Software Engineer',
#     '高级软件开发人员',  # senior software developer
#     'Produktmanager',  # product manager
#     'Científica de datos'  # data scientist
# ]

job_titles = [
    "waitress",
    "Getränke servieren",
    "data scientist",
]

# Get embeddings
embeddings = encode(model, job_titles)

# Calculate cosine similarity matrix
similarities = cos_sim(embeddings, embeddings)
print(similarities)

# match
model.calculate_match(embeddings, embeddings, job_titles, job_titles)
