from typing import Callable
import pandas as pd

from definitions import RequirementsParsingStep, CVParsingStep, MatchingStep, CVMatchingPipeline
from strategies.previous_group import PreviousGroupRequirementsParsing, PreviousGroupCVParsing, PreviousGroupMatching

args = {
    "experience_weight": 1,
    "professional_weight": 1,
    "personal_weight": 1,
    "education_weight": 1,
}
    
applicants = pd.read_csv("data/validation_data/validation_data.csv")
applicants_grouped = applicants.groupby('requirements_path')


pipeline = CVMatchingPipeline(
    RequirementsParsingStep=PreviousGroupRequirementsParsing(),
    CVParsingStep=PreviousGroupCVParsing(),
    MatchingStep=PreviousGroupMatching()
    )

results = pd.DataFrame()
for requirement_path, group in applicants_grouped:
    cv_paths = group['cv_path'].tolist()
    scores = pipeline.run_multiple_cvs(requirement_path, cv_paths, args)
    scores = pd.DataFrame(scores)
    merged = pd.merge(group, scores, on='cv_path')

    results = pd.concat([results, merged], ignore_index=True)
    
results.to_csv("data/validation_data/validation_results.csv", index=False)

