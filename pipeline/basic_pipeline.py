from definitions import CVMatchingPipeline
from strategies.llm import LLMRequirementsParsingStep, LLMCVParsingStep
from strategies.bert import GermanBERTMatchingCategories

pipeline_llm_parsing_previous_matching = CVMatchingPipeline(
    RequirementsParsingStep=LLMRequirementsParsingStep(),
    CVParsingStep=LLMCVParsingStep(),
    MatchingStep=GermanBERTMatchingCategories()
    )