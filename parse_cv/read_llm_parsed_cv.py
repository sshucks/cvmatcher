from definitions import *
import json


class ReadLLMParsedCV(CVParsingStep):
    def run(self, cv_path: str, args) -> CVData:
        """
        Read parsed CV from LLM
        
        :param self: 
        :param cv_path: OS Path to CV (.json)
        :type cv_path: str
        :param args: Optional arguments
        :return: CV Data
        :rtype: CVData
        """
        with open(cv_path, "r", encoding="utf-8") as f:
            cv_data = json.load(f)
        return cv_data