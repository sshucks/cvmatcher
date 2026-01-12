from config import LLM_MODEL, LLM_ENDPOINT, LLM_RANDOM_SEED, LLM_TEMPERATURE, LLM_TOP_K, LLM_TOP_P, APPLICATION_SETTINGS_PATH
import json
class ModelManager:
    """
    Class to manage information regarding the LLM request. Implemented as a Singleton
    Information managed includes:
        - the API endpoint
        - the name of the model to use
        - the random seed to use
        - the temperature (for some consistency in the responses)
        - top k
        - top p
    """
    _uri = LLM_ENDPOINT
    _model_name = None
    _random_seed = LLM_RANDOM_SEED
    _temperature = LLM_TEMPERATURE
    _top_k = LLM_TOP_K
    _top_p = LLM_TOP_P

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
        return cls._instance

    
    def set_uri(self, uri):
        self._instance._uri = uri

    def get_uri(self):
        return self._instance._uri
    

    def get_model_name(self):
        with open(APPLICATION_SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
                llm_settings = settings.get("LLM", {})
        return llm_settings.get("value", "NO MODEL SET")
    
    def set_seed(self, seed):
        self._instance._random_seed = seed

    def get_seed(self):
        return self._instance._random_seed
    
    def set_temperature(self, temperature):
        self._instance._temperature = temperature

    def get_temperature(self):
        return self._instance._temperature
    
    def set_top_k(self, top_k):
        self._instance._top_k = top_k

    def get_top_k(self):
        return self._instance._top_k
    
    def set_top_p(self, top_p):
        self._instance._top_p = top_p

    def get_top_p(self):
        return self._instance._top_p