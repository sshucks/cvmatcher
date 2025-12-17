import pandas as pd
from definitions import CVMatchingPipeline
from parse_cv.read_llm_parsed_cv import ReadLLMParsedCV
from parse_requirements.read_llm_parsed_requirement import ReadLLMParsedRequirement
from strategies.jobbert import GermanEduJobBERTMatchingCategories #, JobBERTMatchingCategories
# from strategies.previous_group import PreviousGroupRequirementsParsing, PreviousGroupCVParsing, PreviousGroupMatching
# from strategies.bert import GermanBERTMatchingCategories


applicants = pd.read_csv("data/validation_data/validation_data.csv")
applicants_grouped = applicants.groupby('requirements_path')


pipeline = CVMatchingPipeline(
    RequirementsParsingStep=ReadLLMParsedRequirement(),
    CVParsingStep=ReadLLMParsedCV(),
    MatchingStep=GermanEduJobBERTMatchingCategories()
    )


results = pd.DataFrame()
for requirement_path, group in applicants_grouped:
    cv_paths = group['cv_path'].tolist()
    cv_paths = [(cv_path, "") for cv_path in cv_paths]
    cv_paths = {"raw": cv_paths, "parsed":[]}
    scores = pipeline.run_multiple_cvs(requirement_path, cv_paths, args={"m":2, "n":3})
    scores = pd.DataFrame(scores)
    merged = pd.merge(group, scores, on='cv_path')
    results = pd.concat([results, merged], ignore_index=True)
    print(results)
    
results.to_csv("data/validation_data/validation_results/LLMParsed_JobBert.csv", index=False)
