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
    embeddingsFile: str,
    language: str
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
    :type embeddingsFile: str
    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str

    :return: Set of all matches ESCO URI
    :rtype: Set[str]
    """

    # gather embeddings
    esco_embeddings = None
    embeddingsPath = f"{ESCO_PATH}/{language}/{embeddingsFile}"
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


def read_occupations(language:str)->pd.DataFrame:
    """
    read occupations and occupation groups from ESCO folder

    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
    
    :return: all occupations and occupation groups, columns: term, uri
    :rtype: pd.DataFrame
    """
    esco_jobs = pd.read_csv(f"{ESCO_PATH}/{language}/occupations_{language}.csv")
    isco_groups = pd.read_csv(f"{ESCO_PATH}/{language}/ISCOGroups_{language}.csv")
    
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


def read_occupation_preferredLabels(language:str)->pd.DataFrame:
    """
    read esco occupations and isco groups, keep only preferred labels for all uris
    
    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
    
    :return: occupations and isco groups, columns: conceptUri, preferredLabel
    :rtype: pd.DataFrame
    """
    esco_jobs = pd.read_csv(f"{ESCO_PATH}/{language}/occupations_{language}.csv")
    isco_groups = pd.read_csv(f"{ESCO_PATH}/{language}/ISCOGroups_{language}.csv")

    esco_isco = pd.concat([esco_jobs[["conceptUri","preferredLabel"]], isco_groups[["conceptUri","preferredLabel"]]])

    return esco_isco



def read_occupation_hierarchy(language:str)->pd.DataFrame:
    """
    read occupations hierarchy from ESCO folder
    
    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
    
    :return: full hierarchy of occupations and their groups, columns: child, parent
    :rtype: pd.DataFrame
    """
    hierarchy = pd.read_csv(f"{ESCO_PATH}/{language}/broaderRelationsOccPillar_{language}.csv")
    lookup = pd.DataFrame({"child":hierarchy["conceptUri"], "parent":hierarchy["broaderUri"]})
    
    return lookup


def get_job_labels(uris:Set[str], job_preferredLabels:pd.DataFrame)->Set[str]:
    """ Function to get the main labels for ESCO occupations

    :param uris: ESCO occupations URI
    :type terms: Set[str]
    :param preferredLabels: occupations and isco groups, columns: conceptUri, preferredLabel
    :type: pd.DataFrame

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    selected = job_preferredLabels[job_preferredLabels['conceptUri'].isin(uris)]

    return set(selected["preferredLabel"])


def get_job_uris(labels:Set[str], job_preferredLabels)->Set[str]:
    """ Function to get the uris for standardized ESCO labels

    :param labels: ESCO occupations labels
    :type terms: Set[str]
    :param preferredLabels: occupations and isco groups, columns: conceptUri, preferredLabel
    :type: pd.DataFrame

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    
    selected = job_preferredLabels[job_preferredLabels['preferredLabel'].isin(labels)]

    return set(selected["conceptUri"])


def read_skills(language:str)->pd.DataFrame:
    """
    read skills and skill groups from ESCO folder

    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
        
    :return: all skills and skill groups, columns: term, uri
    :rtype: pd.DataFrame
    """
    esco_skills = pd.read_csv(f"{ESCO_PATH}/{language}/skills_{language}.csv")
    skill_groups = pd.read_csv(f"{ESCO_PATH}/{language}/skillGroups_{language}.csv")
    
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


def read_skill_hierarchy(language:str)->pd.DataFrame:
    """
    read skills hierarchy from ESCO folder

    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
        
    :return: full hierarchy of skills and their groups, columns: child, parent
    :rtype: pd.DataFrame
    """
    hierarchy = pd.read_csv(f"{ESCO_PATH}/{language}/broaderRelationsSkillPillar_{language}.csv")
    lookup = pd.DataFrame({"child":hierarchy["conceptUri"], "parent":hierarchy["broaderUri"]})
    
    return lookup


def read_skill_occ_relation(language:str)->pd.DataFrame:
    """
    read skill occupation relations from ESCO folder

    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
        
    :return: full relation of occupations and their skills, columns: occupation, skill
    :rtype: pd.DataFrame
    """
    relation = pd.read_csv(f"{ESCO_PATH}/{language}/occupationSkillRelations_{language}.csv")
    lookup = pd.DataFrame({"occupation":relation["occupationUri"], "skill":relation["skillUri"]})
    
    return lookup

def get_skills_for_occ(terms:Set[str], lookup:pd.DataFrame)->Set[str]:
    """ Function to get ESCO skills for ESCO occupations

    :param terms: ESCO occupations
    :type terms: Set[str]
    :param lookup: full relation of occupations and their skills, columns: occupation, skill
    :type: pd.DataFrame

    :return: Set of all related ESCO skills
    :rtype: Set[str]
    """
    skills = set()

    for occ in terms:
        matches = lookup[lookup['occupation'] == occ]

        if matches is not None:
            for m in matches["skill"]:
                skills.add(m)

    return skills
    

def read_skill_preferredLabels(language:str)->pd.DataFrame:
    """
    read esco skills and skill groups, keep only preferred labels for all uris
    
    :param language: language of ESCO to be chosen, en.. English, de.. German
    :type language: str
    
    :return: skills and skill groups, columns: conceptUri, preferredLabel
    :rtype: pd.DataFrame
    """
    esco_skills = pd.read_csv(f"{ESCO_PATH}/{language}/skills_{language}.csv")
    skill_groups = pd.read_csv(f"{ESCO_PATH}/{language}/skillGroups_{language}.csv")

    skills_skillgroups= pd.concat([esco_skills[["conceptUri","preferredLabel"]], skill_groups[["conceptUri","preferredLabel"]]])

    return skills_skillgroups

def get_skill_labels(uris:Set[str], skill_preferredLabels:pd.DataFrame)->Set[str]:
    """ Function to get the main labels for ESCO skills

    :param uris: ESCO skills URI
    :type terms: Set[str]
    :param skill_preferredLabels: skills and skill groups, columns: conceptUri, preferredLabel
    :type: pd.DataFrame

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    selected = skill_preferredLabels[skill_preferredLabels['conceptUri'].isin(uris)]

    return set(selected["preferredLabel"])


def get_skill_uris(labels:Set[str], skill_preferredLabels:pd.DataFrame)->Set[str]:
    """ Function to get the Uris for standardized ESCO Skill labels

    :param uris: ESCO skills URI
    :type terms: Set[str]
    :param skill_preferredLabels: skills and skill groups, columns: conceptUri, preferredLabel
    :type: pd.DataFrame

    :return: Set of all ESCO labels
    :rtype: Set[str]
    """
    selected = skill_preferredLabels[skill_preferredLabels['preferredLabel'].isin(labels)]

    return set(selected["conceptUri"])      

