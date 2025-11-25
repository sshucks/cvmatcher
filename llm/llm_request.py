import json
from typing import Any
import requests
from .model_manager import ModelManager


class Request:
    def __init__(self, model_manager: ModelManager):
        """
        Base class for a simple request towards an LLM endpoint, which expects a JSON response
        :param model_manager: instance of manager that holds model name and endpoint
        """
        self.model_manager = model_manager

    def make_request(self, payload: Any) -> Any:
        raise NotImplementedError()

    def clean_and_parse_json(self, raw_text):
        """
        Extracts the JSON content between '### START ###' and '### END ###'
        and safely parses it.
        """
        if raw_text:
            # remove unnecessary characters
            json_string = (raw_text.strip()
                           .replace('\\n','')
                           .replace('\\"','"')
                           .replace(' ', ' '))

            # try to parse the cleaned string
            parsed_data = json.loads(json_string)
            print("--- Successfully Parsed JSON! ---")
            return parsed_data

        else:
            raise ValueError("Provided JSON string was empty")


class CVParsingRequest(Request):

    #_HEADERS = {"Content-Type": "application/json"}

    def __init__(self, model_manager: ModelManager, system_prompt_path: str, response_schema_path:str):
        """
        Init a request to parse a CV
        :param model_manager: manager that holds connection details and settings for the prompt
        :param system_prompt_path: instructions for the LLM
        :param response_schema_path: expected response JSON format
        """
        super().__init__(model_manager)

        with open(system_prompt_path, "r", encoding='utf-8') as system_prompt_file:
            self.system_prompt = system_prompt_file.read()

        with open(response_schema_path, "rb") as schema:
            self.schema =  json.load(schema)


    def make_request(self, payload: str) -> Any:
        """
        Make the parsing request to the LLM
        :param payload: extracted text of the CV
        :return: JSON object if successful or None in case of errors
        """
        url = self.model_manager.get_uri()
        # configure request
        data = {
            "model": self.model_manager.get_model_name(),
            "stream": False,
            "system": self.system_prompt,
            "prompt": payload,
            "format": self.schema,
            "options": {
                "seed": self.model_manager.get_seed(),
                "temperature": self.model_manager.get_temperature(),
                "top_p": self.model_manager.get_top_p(),
                "top_k": self.model_manager.get_top_k(),
            }
        }
        try:
            # make the request
            response = requests.post(url, json=data)

            # check if the request was successfully
            if response.status_code != 200:
                raise ConnectionError()
            # on successful response, try to parse the json
            return self.clean_and_parse_json(response.json()["response"])

        # catch all errors that can be thrown
        except ConnectionError as e:
            print(f"ERROR: Failed to connect to {url}: {e}")
            return None

        except json.JSONDecodeError as e:
            print(f"ERROR: JSON parsing failed after cleanup: {e}")
            print("The extracted content is not valid JSON.")
            return None

        except ValueError as e:
            print(f"ERROR: the provided JSON string was empty")
            return None

    
class RequirementsParsingRequest(Request):

    #_HEADERS = {"Content-Type": "application/json"}

    def __init__(self, model_manager: ModelManager, system_prompt_path: str, response_schema_path:str):
        """
        Init a request to parse a requirements file
        :param model_manager: manager that holds connection details and settings for the prompt
        :param system_prompt_path: instructions for the LLM
        :param response_schema_path: expected response JSON format
        """
        super().__init__(model_manager)

        with open(system_prompt_path, "r", encoding='utf-8') as system_prompt_file:
            self.system_prompt = system_prompt_file.read()

        with open(response_schema_path, "rb") as schema:
            self.schema = json.load(schema)


    def make_request(self, payload: str) -> Any:
        """
        Make the parsing request to the LLM
        :param payload: extracted text of the requirements file
        :return: JSON object if successful or None in case of errors
        """
        url = self.model_manager.get_uri()
        # configure request
        data = {
            "model": self.model_manager.get_model_name(),
            "stream": False,
            "system": self.system_prompt,
            "prompt": payload,
            "format": self.schema,
            "options": {
                "seed": self.model_manager.get_seed(),
                "temperature": self.model_manager.get_temperature(),
                "top_p": self.model_manager.get_top_p(),
                "top_k": self.model_manager.get_top_k(),
            }
        }
        try:
            # make the request
            response = requests.post(url, json=data)

            # check if the request was successfully
            if response.status_code != 200:
                raise ConnectionError()
            # on successful response, try to parse the json
            return self.clean_and_parse_json(response.json()["response"])

        # catch all errors that can be thrown
        except ConnectionError as e:
            print(f"ERROR: Failed to connect to {url}: {e}")
            return None

        except json.JSONDecodeError as e:
            print(f"ERROR: JSON parsing failed after cleanup: {e}")
            print("The extracted content is not valid JSON.")
            return None

        except ValueError as e:
            print(f"ERROR: the provided JSON string was empty")
            return None

