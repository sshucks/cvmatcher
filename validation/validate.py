from typing import Callable
import pandas as pd

from definitions import RequirementsParsingStep, CVParsingStep, MatchingStep, CVMatchingPipeline
from strategies.previous_group import PreviousGroupRequirementsParsing, PreviousGroupCVParsing, PreviousGroupMatching
from strategies.llm import LLMCVParsingStep, LLMRequirementsParsingStep
applicants = pd.read_csv("./data/validation_data/validation_data.csv")
applicants = applicants[(applicants['cv_path'].str.contains("11627")) |(applicants['cv_path'].str.contains("11877")) ]
applicants_grouped = applicants.groupby('requirements_path')


pipeline = CVMatchingPipeline(
    RequirementsParsingStep=LLMRequirementsParsingStep(), #PreviousGroupRequirementsParsing(),
    CVParsingStep=LLMCVParsingStep(),#PreviousGroupCVParsing(),
    MatchingStep=PreviousGroupMatching()
    )



results = pd.DataFrame()
for requirement_path, group in applicants_grouped:
    cv_paths = group['cv_path'].tolist()
    scores = pipeline.run_multiple_cvs(requirement_path, cv_paths, args={"m":2, "n":3})
    scores = pd.DataFrame(scores)
    merged = pd.merge(group, scores, on='cv_path')
    results = pd.concat([results, merged], ignore_index=True)
    
results.to_csv("./data/validation_data/validation_results/previous_group.csv", index=False)