from typing import Callable
import pandas as pd

from definitions import RequirementsParsingStep, CVParsingStep, MatchingStep, CVMatchingPipeline
from parse_cv.read_llm_parsed_cv import ReadLLMParsedCV
from parse_requirements.read_llm_parsed_requirement import ReadLLMParsedRequirement
from strategies.previous_group import PreviousGroupRequirementsParsing, PreviousGroupCVParsing, PreviousGroupMatching
applicants = pd.read_csv("data/validation_data/validation_data.csv")
applicants_grouped = applicants.groupby('requirements_path')


pipeline = CVMatchingPipeline(
    RequirementsParsingStep=ReadLLMParsedRequirement(),
    CVParsingStep=ReadLLMParsedCV(),
    MatchingStep=PreviousGroupMatching()
    )

results = pd.DataFrame()
for requirement_path, group in applicants_grouped:
    cv_paths = group['cv_path'].tolist()
    scores = pipeline.run_multiple_cvs(requirement_path, cv_paths)
    scores = pd.DataFrame(scores)
    merged = pd.merge(group, scores, on='cv_path')
    results = pd.concat([results, merged], ignore_index=True)
    
    results.to_csv("data/validation_data/validation_results/LLMParsed_PreviousGroup.csv", index=False)