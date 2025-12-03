from typing import TypedDict

import utils, os, json
from caching.CachingMixin import PersistingMixin
from config import (LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_DE, 
                    LLM_PARSED_REQUIREMENTS_SCHEMA, 
                    LLM_SYSTEM_PROMPT_PATH_CV_PARSING_DE, 
                    LLM_PARSED_CV_SCHEMA, CV_OUTPUT_DIR)

from definitions import RequirementsParsingStep, RequirementsData, CVParsingStep, CVData
from llm.majority_voting import MajorityVoting, ObjectMajoritVotingStrategy
from parse_requirements.llm import extract_requirements as parse_requirements
from parse_cv.llm import extract_cv as parse_cv
from llm import ListIntersectionMajorityVotingStrategy, ListObjectMajorityVotingStrategy, \
    SingleValueMajorityVotingStrategy

class LLMRequirementsParsingStep(RequirementsParsingStep):
    def run(self, requirements_path: str, args) -> RequirementsData:
        """
        Parse a single requirements file
        :param requirements_path: path to the requirements file
        :param args: dictionary, expected to contain m (minimum number of documents to share information)
        and n (number of documents), which are used in Majority Voting
        :return: RequirementsData
        """
        m = args['m']
        n = args['n']

        # read requirements file and use important part of the file to reduce tokens
        content = utils.read_pdf(requirements_path)
        content = content.split("Umfeld der Position im Unternehmen")[0]

        try:
            # call the LLM parsing multiple times because of none deterministic results
            intermediate_results = []
            for i in range(1, n + 1):
                result_i = parse_requirements.extract_requirements(content=content, system_prompt_path=LLM_SYSTEM_PROMPT_PATH_REQUIREMENTS_PARSING_DE, schema_path = LLM_PARSED_REQUIREMENTS_SCHEMA)
                if result_i is not None:
                    intermediate_results.append(result_i)
                else:
                    raise ValueError("LLM could not parse file, response was None")

            # perform majority voting on the results
            mapping = {
                'education': ListObjectMajorityVotingStrategy(key="education",
                                                            id_parts=['field_of_study', 'degree']),
                'professional_experience': ListObjectMajorityVotingStrategy(key="professional_experience",
                                                                            id_parts=['job_title', 'duration', 'industry']),
                'hard_skills': ListIntersectionMajorityVotingStrategy(key="hard_skills"),
                'soft_skills': ListIntersectionMajorityVotingStrategy(key="soft_skills"),
                'job_title': SingleValueMajorityVotingStrategy(key='job_title')
            }

            m_voting = MajorityVoting(m=m, n=n)
            m_voting.set_strategies(mapping=mapping)
            aggregated_result = m_voting.apply_voting(intermediate_results)

            # return results
            return aggregated_result
        except ValueError as e:
            print(f"An error occured: {repr(e)}")

class LLMCVParsingStep(CVParsingStep, PersistingMixin):
    
    def run(self, cv_path: str, args) -> CVData:
        """
        Parse a single cv file
        :param cv_path: path to the CV file
        :param args: dictionary, expected to contain m (minimum number of documents to share information)
        and n (number of documents), which are used in Majority Voting
        :return: RequirementsData
        """
        m = args['m']
        n = args['n']

        # read cv file
        content = utils.read_pdf(cv_path)

        try:
            # call the LLM parsing multiple times because of none deterministic results
            intermediate_results = []
            for i in range(1, n + 1):
                result_i = parse_cv.extract_cv(content=content,
                                                system_prompt_path=LLM_SYSTEM_PROMPT_PATH_CV_PARSING_DE,
                                                schema_path=LLM_PARSED_CV_SCHEMA)
                if result_i is not None:
                    intermediate_results.append(result_i)
                else:
                        raise ValueError("LLM could not parse file, response was None")

            # perform majority voting on the results
            mapping = {
                'education': ListObjectMajorityVotingStrategy(key="education",
                                                            id_parts=['field_of_study', 'graduated']),
                'professional_experience': ListObjectMajorityVotingStrategy(key="professional_experience",
                                                                            id_parts=['job_title', 'start', 'end'],
                                                                            list_aggreagte=['responsibilities']),
                'hard_skills': ListIntersectionMajorityVotingStrategy(key="hard_skills"),
                'soft_skills': ListIntersectionMajorityVotingStrategy(key="soft_skills"),
                'personal': ObjectMajoritVotingStrategy(key="personal"),
            }

            m_voting = MajorityVoting(m=m, n=n)
            m_voting.set_strategies(mapping=mapping)
            aggregated_result = m_voting.apply_voting(intermediate_results)

            # persist the aggreagted data
            filename = os.path.basename(cv_path)
            self.persist_data(filename=filename, dest=CV_OUTPUT_DIR, data=aggregated_result)

            return aggregated_result
        
        except ValueError as e:
            print(f"An error occured: {repr(e)}")

    def persist_data(self, filename:str, dest:str, data:dict):
        
        os.makedirs(dest, exist_ok=True)
        path = os.path.join(dest, filename+".json")

        with open(path, "w", encoding='utf-8') as response:
            response.write(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))


