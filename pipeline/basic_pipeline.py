from definitions import CVMatchingPipeline
from strategies.llm import LLMRequirementsParsingStep, LLMCVParsingStep
from strategies.previous_group import PreviousGroupMatching

pipeline = CVMatchingPipeline(
    RequirementsParsingStep=LLMRequirementsParsingStep(),
    CVParsingStep=LLMCVParsingStep(),
    MatchingStep=PreviousGroupMatching()
    )