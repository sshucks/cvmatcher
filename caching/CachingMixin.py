from typing import TypedDict


class PersistingMixin:
    def persist_data(self,filename:str, dest:str, data:dict):
        pass