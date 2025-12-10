from definitions import *
import json


class ReadLLMParsedRequirement(CVParsingStep):
    def run(self, req_path: str, args) -> RequirementsData:
        """
        Read parsed Requirement from LLM
        
        :param self: 
        :param req_path: OS Path to Requirement (.json)
        :type req_path: str
        :param args: Optional arguments
        :return: Requirements Data
        :rtype: RequirementsData
        """
        with open(req_path, "r", encoding="utf-8") as f:
            req_data = json.load(f)
        return req_data
