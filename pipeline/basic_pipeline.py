from definitions import CVMatchingPipeline
from strategies.llm_parsing import LLMRequirementsParsingStep, LLMCVParsingStep
from strategies.llm_matching import LLMPartlyMatching

pipeline_llm_parsing_previous_matching = CVMatchingPipeline(
    RequirementsParsingStep=LLMRequirementsParsingStep(),
    CVParsingStep=LLMCVParsingStep(),
    MatchingStep=LLMPartlyMatching()
    )