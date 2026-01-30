import warnings
from fastapi import FastAPI, Body
from bert.jobbert import JobBERTMatchingStep

app = FastAPI()

matching_step = JobBERTMatchingStep()

category_matchings = {
    "education": matching_step,
    "professional_experience": matching_step,
    "hard_skills": matching_step,
    "soft_skills": matching_step
}

def normalize(weights):
    """
    Normalize a dictionary of weights so that they sum to 1.
    
    :param weights: Dictionary of weights to normalize
    :type weights: dict
    :return: Normalized weights
    :rtype: dict
    """
    total_weight = sum(weights.values())
    return {k: v / total_weight for k, v in weights.items()}

def run(cv_data, requirements, weights) -> tuple[float, dict]:
    """
    Perform matching across multiple categories and compute a final score.
    
    :param self:
    :param cv_data: Parsed CV data
    :type cv_data: CVData
    :param requirements: Parsed requirements data
    :type requirements: RequirementsData
    :param weights: Weights for categories
        education_weight: Weight for education category
        professional_experience_weight: Weight for professional experience category
        hard_skills_weight: Weight for hard skills category
        soft_skills_weight: Weight for soft skills category
    :return: Final matching score and individual category scores
    :rtype: tuple[float, dict]
    """
    
    category_args = normalize(weights)

    # Perform matching for each category and collect scores
    scores = {}
    weighted_scores = {}
    weights = {}
    

    for category, weight in category_args.items():
        
        # get cv and requirements section for the category
        cv_section = cv_data[category]
        requirements_section = requirements[category]

        # if both entries exist, perform matching
        if cv_section and requirements_section:
            weights[category] = weight
            score = category_matchings[category].run(cv_section, requirements_section)
            print(f"{category}-score: {score}")

            scores[category] = score

            if score is None:
                weights[category] = 0

        # if one of them is empty, set weight for this category to 0 and issue warning
        else:
            weights[category] = 0
            if not cv_section:
                warnings.warn(f"CV data for '{category}' is empty.")

            if not requirements_section:
                warnings.warn(
                    f"Requirements data for '{category}' is empty.")
    
    print(f"scores: {scores}")

    # normalize weights again after removing empty sections
    normalized_weights = normalize(weights)

    # calculate weighted scores
    weighted_scores = {
        category: score * normalized_weights[category]
        for category, score in scores.items()
    }

    # calculate final score
    final_score = sum(weighted_scores.values())
    print(f"final_score: {final_score}")

    return final_score, scores

    
@app.post("/matching")
def matching_endpoint(cv_data: list[dict] = Body(...), requirements: dict = Body(...), weights: dict = Body(...)) -> list[dict]:
    results = []
    for single_cv_data in cv_data:
        # try:
        final_score, scores = run(single_cv_data, requirements, weights)
        results.append({
            "final_score": final_score,
            **scores,
            "file_hash": single_cv_data.get("file_hash", None)
        })
        # except Exception as e:
        #     # write warning message
        #     warnings.warn(f"Error processing CV data: {e}")
    return results


