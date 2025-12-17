from definitions import CVData, RequirementsData, MatchingStep
from typing import Any
from llm.llm_request import MatchingRequest
from llm.model_manager import ModelManager
from llm.majority_voting import MajorityVoting, SingleValueMajorityVotingStrategy

class LLMPartlyMatchingStep(MatchingStep):

    def __init__(self,system_prompt_path:str, response_schema_path:str):
        self.system_prompt_path = system_prompt_path
        self.response_schema_path = response_schema_path

    def run(self, cv_data_part: list[Any], req_data_part: list[Any], args) -> float:
        """
        Match the given CV to the given requirements data and return a 
        """
        n = args.get('n')
        m = args.get('m')

        try:
            intermediate_results = []
            matching_request = MatchingRequest(model_manager=ModelManager(),
                                                    system_prompt_path=self.system_prompt_path,
                                                    response_schema_path=self.response_schema_path)
            for i in range(1, n + 1):
                result_i = matching_request.make_request(cv_data_part, req_data_part)
                if result_i is not None:
                    intermediate_results.append(result_i)
                else:
                    raise ValueError("LLM could not parse file, response was None")
            
            # perform majority voting on the results
            mapping = {
                'score' : SingleValueMajorityVotingStrategy(key='score')
            }

            m_voting = MajorityVoting(m=m, n=n)
            m_voting.set_strategies(mapping=mapping)
            aggregated_result = m_voting.apply_voting(intermediate_results)
            
            # take first of majority voted score
            if aggregated_result['score']:
                # take the verbal explanation of the first result that shares this score
                aggregated_result['verbal_explanation'] = [r for r in intermediate_results if aggregated_result['score'] == r['score']][0]
            else:
                raise ValueError("No score was returned from the LLM")

            # return results
            print(f"result:",aggregated_result)
            return aggregated_result
         
        except ValueError as e:
            print(f"An error occured: {repr(e)}")

class LLMFullMatchingStep(MatchingStep):

    def __init__(self,system_prompt_path:str, response_schema_path:str):
        self.system_prompt_path = system_prompt_path
        self.response_schema_path = response_schema_path

    def run(self, cv_data: CVData, req_data: RequirementsData, args) -> float:
        """
        Match the given CV to the given requirements data and return a 
        """
        n = args.get('n')
        m = args.get('m')

        try:
            intermediate_results = []
            matching_request = MatchingRequest(model_manager=ModelManager(),
                                                    system_prompt_path=self.system_prompt_path,
                                                    response_schema_path=self.response_schema_path)
            for i in range(1, n + 1):
                result_i = matching_request.make_request(cv_data, req_data)
                if result_i is not None:
                    intermediate_results.append(result_i)
                else:
                    raise ValueError("LLM could not parse file, response was None")
            
            # perform majority voting on the results
            mapping = {
                'score' : SingleValueMajorityVotingStrategy(key='score')
            }

            m_voting = MajorityVoting(m=m, n=n)
            m_voting.set_strategies(mapping=mapping)
            aggregated_result = m_voting.apply_voting(intermediate_results)
            
            # take first of majority voted score
            if aggregated_result['score']:
                # take the verbal explanation of the first result that shares this score
                aggregated_result['verbal_explanation'] = [r for r in intermediate_results if aggregated_result['score'] == r['score']][0]
            else:
                raise ValueError("No score was returned from the LLM")

            # return results
            return aggregated_result
         
        except ValueError as e:
            print(f"An error occured: {repr(e)}")