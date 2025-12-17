from definitions import CVParsingStep, RequirementsData
import json


class ReadLLMParsedRequirement(CVParsingStep):
    def run(self, req_path: str, args) -> RequirementsData:
        """
        Read parsed Requirement from LLM
        
        :param self: 
        :param req_path: OS Path to Requirement (.docx)
        :type req_path: str
        :param args: Optional arguments
        :return: Requirements Data
        :rtype: RequirementsData
        """

        req_path_parsed = req_path.replace("raw_data", "parsed_data").replace(".docx", ".docx.json")

        with open(req_path_parsed, "r", encoding="utf-8") as f:
            req_data = json.load(f)
        return req_data
