from definitions import *
import json


class ReadLLMParsedCV(CVParsingStep):
    def run(self, cv_path: str) -> CVData:
        """
        Read parsed CV from LLM
        
        :param self: 
        :param cv_path: OS Path to CV (.pdf or .docx)
        :type cv_path: str
        :return: CV Data
        :rtype: CVData
        """

        cv_path_parsed = cv_path.replace("raw_data", "parsed_data").replace(".docx", ".docx.json").replace(".pdf", ".pdf.json")

        try:
            with open(cv_path_parsed, "r", encoding="utf-8") as f:
                cv_data = json.load(f)
            return cv_data
        except FileNotFoundError as e:
            print(f"File {cv_path_parsed} does not exist: {e}")