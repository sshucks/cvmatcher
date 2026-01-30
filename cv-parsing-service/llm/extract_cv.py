from llm import CVParsingRequest, ModelManager
def extract_cv(content: str, system_prompt_path: str, schema_path:str):
    """
    Extract the CV information using an LLM
    :param content: content of the CV
    :param system_prompt_path: path to the file containing the system prompt for CV parsing
    :param schema_path: path to the JSON schema describing the CV response
    :return:
    """
    parsing_request = CVParsingRequest(model_manager=ModelManager(),
                                                 system_prompt_path=system_prompt_path,
                                                 response_schema_path=schema_path)
    return parsing_request.make_request(content)