from pydantic import BaseModel,EmailStr 
# Emailstr validates the email.
from typing import Dict
from datetime import datetime

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
    username:str
    age:int 
    gender:str
    

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

   



# For implementing the jwt part  
class UserCreate(BaseModel):
    name: str
    age : int 
    gender : str
    email: EmailStr  # Validates proper email format
    hashed_password: str
    class Config:
        orm_mode = True


class UserResponse(BaseModel):
    name: str
    email: str
    message: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    username:str
    age: int
    gender: str
    token_type: str


class UserInfo(BaseModel):
    name: str
    age: int
    gender: str



# Test related models 

class TestHistoryResponse(BaseModel):
    test_id: int
    date: datetime
    userinput: str
    response: str

    class Config:
        orm_mode = True
