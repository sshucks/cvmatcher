class CachedCV_Wrapper:
    def __init__(self, hash_digest:str, file_path:str, already_extracted:bool):
        self.hash_digest = hash_digest
        self.file_path = file_path
        self.already_extracted = already_extracted
    
    def get_hash_digest(self):
        return self.hash_digest
    
    def get_file_path(self):
        return self.file_path
    
    def is_extracted(self):
        return self.already_extracted
    
    def __str__(self):
        return f"CachedCV_Wrapper[hash_digest={self.hash_digest}, file_path = {self.file_path}, is_extracted={self.already_extracted}]"