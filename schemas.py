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

class TextInput(BaseModel):
    text: str


class TokenRequest(BaseModel):
    token: str
    class Config:
        orm_mode = True


class TokenRequestRegister(BaseModel):
    token: str
    name: str 
    age: int
    gender: str

    class Config:
        orm_mode = True