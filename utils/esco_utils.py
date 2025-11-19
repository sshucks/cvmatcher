import pandas as pd
import os
import numpy as np
import torch
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import batch_to_device, cos_sim
from typing import List, Set
from config import ESCO_PATH


def encode_batch(model:SentenceTransformer, texts:List[str])->np.array:
    """
    :param model: Transformermodel to calculate embeddings
    :type model: SentenceTransformer
    :param texts: Terms to encode
    :type texts: List[str]
    """
    features = model.tokenize(texts)
    features = batch_to_device(features, model.device)
    features["text_keys"] = ["anchor"]
    with torch.no_grad():
        out_features = model.forward(features)
    return out_features["sentence_embedding"].cpu().numpy()


def encode(model:SentenceTransformer, texts:List[str], batch_size: int = 8)->np.array:
    embeddings = []
    
    # Encode in batches
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        embeddings.append(encode_batch(model, batch))
    
    # Concatenate embeddings
    embeddings = np.concatenate(embeddings)
    return embeddings


def ESCO_labelling(
    terms: List[str],
    esco: pd.DataFrame,
    model: SentenceTransformer,
    threshold: float,
    max_terms: int,
    embeddingsFile: str
) -> Set[str]:
    """ Function for labelling jobs or skills

    :param terms: terms that should be labelled (jobs or skills)
    :type terms: List[str]
    :param esco: all esco terms that are used for labelling (columns: term, uri), also includes synonyms
    :type esco pd.DataFrame
    :param model: Transformermodel to calculate embeddings
    :type model: SentenceTransformer
    :param threshold: minimal cosine similarity score to be considered a match
    :type threshold: float
    :param max_terms: max number of matches to keep per term
    :type max_terms: int
    :param embeddingsFile: where to load the esco embeddings from (or calculate and save to, if not existing)
    :type embeddingsPath: str

    :return: Set of all matches ESCO URI
    :rtype: Set[str]
    """

    # gather embeddings
    esco_embeddings = None
    embeddingsPath = f"{ESCO_PATH}/{embeddingsFile}"
    if os.path.exists(embeddingsPath):
        esco_embeddings = np.load(embeddingsPath)

    else:
        esco_embeddings = encode(model, list(esco["term"]))
        np.save(embeddingsPath, esco_embeddings)
        
    term_embeddings = encode(model, terms)

    # matching
    similarities = cos_sim(term_embeddings, esco_embeddings)


    # Thresholding the matches
    matches = np.where(similarities > threshold)
    esco_matches = np.array(esco["uri"])[matches[1]]
    term_matches = np.array(terms)[matches[0]]
    scores = np.array(similarities[matches])

    # Limiting the matches to the best n = max_terms matches per term
    match_df = pd.DataFrame({"term":term_matches, "esco":esco_matches, "score": scores})
    match_df = match_df.groupby(["term","esco"]).max("score")

    match_df = (match_df.sort_values("score", ascending=False)
                      .groupby(level=0)
                      .head(max_terms))
    
    match_df = match_df.reset_index().sort_values(by=["term"])

    return set(match_df["esco"])


def enrich_ESCO(terms:Set[str], lookup:pd.DataFrame)->Set[str]:
    """ Function to enrich ESCO terms with broader hierarchical categories

    :param terms: terms that should be enriched
    :type terms: Set[str]
    :param lookup: relations table, columns: child, parent
    :type lookup: pd.DataFrame

    :return: Set of all terms including the new categorical terms
    :rtype: Set[str]
    """

    new_terms = set()

    for term in terms:
        child = term
        while (lookup['child'] == child).any():
            parent = lookup[lookup['child'] == child].iloc[0]["parent"]
            new_terms.add(parent)
            child = parent

    return terms | new_terms


def hierarchical_matching(requirements:Set[str], cv_labels:Set[str], lookup:pd.DataFrame, hierarchical_decay:float):
    """ Function to match requirements and cv_labels

    :param requirements: ESCO labels of requirements
    :type requirements: Set[str]
    :param cv_labels: ESCO labels of CV
    :type cv_labels: Set[str]
    :param lookup: relations table, columns: child, parent
    :type lookup: pd.DataFrame
    :param hierarchical_decay: Hyperparameter to model the score values of broader hierarchical matches
    :type hierarchical_decay: float

    :return: Value 0-1, how well are the requirements covered in the cv
    :rtype: float
    """
    enriched_labels = enrich_ESCO(cv_labels, lookup)

    matches = []
    score = 0

    for r in requirements:
        done = False
        weight = 1
        term = r
        
        while not done:
            if term in enriched_labels:
                score += weight
                done = True
                matches.append(term)
            else:
                weight = weight * hierarchical_decay
                if term in lookup['child'].values:
                    term = lookup[lookup['child'] == term].iloc[0]["parent"]
                else:
                    done = True
    
    return(score/len(requirements), matches)


def read_occupations()->pd.DataFrame:
    """
    read occupations and occupation groups from ESCO folder
    
    :return: all occupations and occupation groups, columns: term, uri
    :rtype: pd.DataFrame
    """
    esco_jobs = pd.read_csv(f"{ESCO_PATH}/occupations_de.csv")
    isco_groups = pd.read_csv(f"{ESCO_PATH}/ISCOGroups_de.csv")
    
    job_dict = {}
    for row in esco_jobs.iterrows():
        all_labels = [row[1]["preferredLabel"]]
    
        if pd.notna(row[1]["altLabels"]):
            all_labels += row[1]["altLabels"].split("\n")
    
        if pd.notna(row[1]["hiddenLabels"]):
            all_labels += row[1]["hiddenLabels"].split("\n")
    
        new = {l:row[1]["conceptUri"] for l in all_labels}
        job_dict = job_dict | new
    
    for row in isco_groups.iterrows():
        job_dict[row[1]["preferredLabel"]] = row[1]["conceptUri"]

    return pd.DataFrame({"term":job_dict.keys(), "uri":job_dict.values()})


def read_occupation_hierarchy()->pd.DataFrame:
    """
    read occupations hierarchy from ESCO folder
        
    :return: full hierarchy of occupations and their groups, columns: child, parent
    :rtype: pd.DataFrame
    """
    hierarchy = pd.read_csv(f"{ESCO_PATH}/broaderRelationsOccPillar_de.csv")
    lookup = pd.DataFrame({"child":hierarchy["conceptUri"], "parent":hierarchy["broaderUri"]})
    
    return lookup


def get_job_labels(uris:Set[str])->Set[str]:
    """ Function to get the main labels for ESCO occupations

    :param uris: ESCO occupations URI
    :type terms: Set[str]

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    esco_jobs = pd.read_csv(f"{ESCO_PATH}/occupations_de.csv")
    isco_groups = pd.read_csv(f"{ESCO_PATH}/ISCOGroups_de.csv")

    esco_isco = pd.concat([esco_jobs[["conceptUri","preferredLabel"]], isco_groups[["conceptUri","preferredLabel"]]])
    selected = esco_isco[esco_isco['conceptUri'].isin(uris)]

    return set(selected["preferredLabel"])


def read_skills()->pd.DataFrame:
    """
    read skills and skill groups from ESCO folder
        
    :return: all skills and skill groups, columns: term, uri
    :rtype: pd.DataFrame
    """
    esco_skills = pd.read_csv(f"{ESCO_PATH}/skills_de.csv")
    skill_groups = pd.read_csv(f"{ESCO_PATH}/skillGroups_de.csv")
    
    skill_dict = {}
    for row in esco_skills.iterrows():
        all_labels = [row[1]["preferredLabel"]]
    
        if pd.notna(row[1]["altLabels"]):
            all_labels += row[1]["altLabels"].split("\n")
    
        if pd.notna(row[1]["hiddenLabels"]):
            all_labels += row[1]["hiddenLabels"].split("\n")
    
        new = {l:row[1]["conceptUri"] for l in all_labels}
        skill_dict = skill_dict | new
    
    for row in skill_groups.iterrows():
        all_labels = [row[1]["preferredLabel"]]
    
        if pd.notna(row[1]["altLabels"]):
            all_labels += row[1]["altLabels"].split("\n")
    
        if pd.notna(row[1]["hiddenLabels"]):
            all_labels += row[1]["hiddenLabels"].split("\n")
    
        new = {l:row[1]["conceptUri"] for l in all_labels}
        skill_dict = skill_dict | new

    return pd.DataFrame({"term":skill_dict.keys(), "uri":skill_dict.values()})


def read_skill_hierarchy(e)->pd.DataFrame:
    """
    read skills hierarchy from ESCO folder
        
    :return: full hierarchy of skills and their groups, columns: child, parent
    :rtype: pd.DataFrame
    """
    hierarchy = pd.read_csv(f"{ESCO_PATH}/broaderRelationsSkillPillar_de.csv")
    lookup = pd.DataFrame({"child":hierarchy["conceptUri"], "parent":hierarchy["broaderUri"]})
    
    return lookup


def read_skill_occ_relation()->pd.DataFrame:
    """
    read skill occupation relations from ESCO folder
        
    :return: full relation of occupations and their skills, columns: occupation, skill
    :rtype: pd.DataFrame
    """
    relation = pd.read_csv(f"{ESCO_PATH}/occupationSkillRelations_de.csv")
    lookup = pd.DataFrame({"occupation":relation["occupationUri"], "skill":relation["skillUri"]})
    
    return lookup

def get_skills_for_occ(terms:Set[str])->Set[str]:
    """ Function to get ESCO skills for ESCO occupations

    :param terms: ESCO occupations
    :type terms: Set[str]

    :return: Set of all related ESCO skills
    :rtype: Set[str]
    """
    lookup = read_skill_occ_relation()
    skills = set()

    for occ in terms:
        matches = lookup[lookup['occupation'] == occ]

        if matches is not None:
            for m in matches["skill"]:
                skills.add(m)

    return skills
    

def get_skill_labels(uris:Set[str])->Set[str]:
    """ Function to get the main labels for ESCO skills

    :param uris: ESCO skills URI
    :type terms: Set[str]
    :param esco_path: path to ESCO folder
    :type esco_path: str

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    esco_skills = pd.read_csv(f"{ESCO_PATH}/skills_de.csv")

    selected = esco_skills[esco_skills['conceptUri'].isin(uris)]

    return set(selected["preferredLabel"])        

