from fastapi import FastAPI,HTTPException,Depends,Request,BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from Assessment.main import Assess
from accessories.exception import CustomException
from pydantic import BaseModel
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import sys


#imports that may be shifted
from accessories.utils import load_json


load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")
BASE_URL = os.getenv("BASE_URL")

class TextInput(BaseModel):
    text: str

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or specify your domain
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/assess_text/")
async def take_input(request: Request,  input: TextInput):
    try:
        text = input.text
        if text=="": 
            return JSONResponse(content={"disorder": "no disorder"})
        testing = Assess(text)  
        isthere = testing.classify_dual()  

        if  isthere == "Neutral Statement":
            return JSONResponse(content={"disorder": "no disorder"})  

        disorders = testing.dignose()
        file_path = os.path.join(os.getcwd(), 'Assessment', 'mapping.json')
        with open(file_path, 'r') as file:
            mapping_data = json.load(file)
        res_file = {}
        for disorder in disorders:
            if(disorder == "No disorder found"):
                return JSONResponse(content={"disorder": "no disorder"})

            res_file[disorder] = mapping_data["Mental_Health_Tests"][disorder]
    
        return JSONResponse(content={"disorder": res_file}) 

    except Exception as e:
        raise CustomException(e, sys)
    
