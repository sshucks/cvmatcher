from llm import RequirementsParsingRequest, ModelManager
def extract_requirements(content: str, system_prompt_path: str, schema_path:str):
    """
    Extract the requirements information using an LLM
    :param content: content of the requirements file
    :param system_prompt_path: path to the file containing the system prompt for requirements parsing
    :param schema_path: path to the JSON schema describing the requirements response
    :return:
    """
    parsing_request = RequirementsParsingRequest(model_manager=ModelManager(),
                                                 system_prompt_path=system_prompt_path,
                                                 response_schema_path=schema_path)
    return parsing_request.make_request(content)