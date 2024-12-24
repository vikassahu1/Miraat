from pydantic import BaseModel
from typing import Dict

class TestRequest(BaseModel):
    disorder_name: str
    sub_category: str
    test: str

class TestAndAnswer(BaseModel):
    test_name: str
    subcategory:str 
    answers: Dict[str, int]

class solRequest(BaseModel):
    context: str