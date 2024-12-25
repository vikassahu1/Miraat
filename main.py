from fastapi import FastAPI,HTTPException,Depends,Request,BackgroundTasks
from fastapi.responses import JSONResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles



from Assessment.main import Assess
from accessories.exception import CustomException
from llm_setup.main import LLMSetup
from pydantic import BaseModel
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import json
import sys


#imports that may be shifted
from accessories.utils import load_json
from accessories.logger import logging
from schemas import TestRequest,TestAndAnswer,solRequest
from Assessment.test_inference import get_inference



load_dotenv()


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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



# Rendering html paegs 
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})


@app.get("/assessment")
async def assessment(request: Request):
    return templates.TemplateResponse("assessment.html", {"request": request})










# Post request pages 
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





# To get the questions for a specific test we are using abbrevoiation mapping. 
@app.post("/get_test_questions/")
async def get_questions(data: TestRequest):
    try:
        # Extract the test name from the request
        test_name = data.test

        # Load the abbreviation mapping file
        file_path = os.path.join(os.getcwd(), 'Assessment', 'abbreviation_map.json')
        with open(file_path, 'r') as file:
            mapping_data = json.load(file)

        # Check if the test name exists in the mapping
        if test_name not in mapping_data:
            return JSONResponse(
                content={"error": f"Test '{test_name}' not found in abbreviation mapping."},
                status_code=404
            )

        # Map to the actual test name
        test_name = mapping_data[test_name]

        # Load the test data file
        file_path = os.path.join(os.getcwd(), 'Assessment', 'test_data.json')
        with open(file_path, 'r') as file:
            test_data = json.load(file)

        # Check if the mapped test name exists in test data
        if test_name not in test_data:
            return JSONResponse(
                content={"error": f"No questions found for test '{test_name}'."},
                status_code=404
            )

        # Retrieve the questions for the test
        questions = test_data[test_name]
        return JSONResponse(content={"questions": questions}, status_code=200)

    except FileNotFoundError as fnf_error:
        # Handle specific file not found errors
        return JSONResponse(
            content={"error": f"Required file missing: {str(fnf_error)}"},
            status_code=500
        )
    except json.JSONDecodeError as json_error:
        # Handle JSON parsing errors
        return JSONResponse(
            content={"error": f"Error parsing JSON file: {str(json_error)}"},
            status_code=500
        )
    except Exception as e:
        # Handle generic errors
        return JSONResponse(
            content={"error": f"An unexpected error occurred: {str(e)}"},
            status_code=500
        )







@app.post("/get_inference_from_test/")
async def get_inference_from_test(request: TestAndAnswer):
    try:
        # Directly access the validated Pydantic model
        test_name = request.test_name
        answers = request.answers
        subcategory = request.subcategory
        
        if not test_name or not answers:
            raise HTTPException(status_code=400, detail="Missing test name or answers")
        
        # Call inference function
        score, inference = get_inference(test_name, answers)
        
        return JSONResponse(
            content={
                "score": score, 
                "inference": inference
            }
        )
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in get_inference_from_test: {e}")
        raise HTTPException(status_code=500, detail=str(e))



    
    
@app.post("/get_solution_text/")
async def get_solution_text(text: solRequest):
    text = text.context
    logging.info(text)
    try:
        set_up = LLMSetup()
        solution_html = set_up.get_result(text)
        logging.info(solution_html)

        return JSONResponse(
            content={
                "solution_text": solution_html
            }
        )
    except Exception as e:
        print(f"Error in get_solution_text: {e}")
        raise HTTPException(status_code=500, detail=str(e))
