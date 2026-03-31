from pydantic import BaseModel
from typing import Optional

class PromptRequest(BaseModel):
    prompt: str
    user_id:Optional[int]=None
    schema_name:str

class RagRequest(BaseModel):
    question:str
    database_name:str