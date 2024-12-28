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
from schemas import TestRequest,TestAndAnswer,solRequest,TokenRequest,TextInput
from Assessment.test_inference import get_inference


# Database imports 
from database import User, Base, engine, SessionLocal
from sqlalchemy.orm import Session 
from firebase_admin import auth, credentials, initialize_app
from sqlalchemy.exc import SQLAlchemyError



load_dotenv()


app = FastAPI()
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
cred = credentials.Certificate("miraat-54aac-firebase-adminsdk-9r6ms-cfe53c0902.json")
initialize_app(cred)
BASE_URL = os.getenv("BASE_URL")



# Dependency to get database session
def get_db():
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        raise
    finally:
        db.close()






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







@app.get("/helplines")
async def get_helplines(request: Request):
    try:
        file_path = os.path.join(os.getcwd(), 'accessories', 'helplines.json')
        with open(file_path, 'r') as file:
            data = json.load(file)

        helplines = data.get("helplines", {})

    except Exception as e:
        return {"error": str(e)}

    # Pass helpline data to the template
    return templates.TemplateResponse("helplines.html", {"request": request, "helplines": helplines})
        





# Login Systems 

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})





@app.post("/verify-token/")
async def verify_token(request: TokenRequest, db: Session = Depends(get_db)):
    try:
        decoded_token = auth.verify_id_token(request.token)
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        # More detailed logging
        print(f"UID: {uid}")
        print(f"Email: {email}")
        print(f"Full decoded token: {decoded_token}")

        # Explicit error handling
        if not uid or not email:
            raise ValueError("Missing UID or email in token")

        # User creation/verification logic
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            new_user = User(id=uid, email=email, name=decoded_token.get("name", ""))
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return {"message": "New user created", "email": new_user.email}

        return {"message": "User verified", "email": user.email}
    except Exception as e:
        print(f"Detailed error during token verification: {e}")
        raise HTTPException(status_code=401, detail=str(e))





@app.post("/register-user/")
async def register_user(request: TokenRequest, db: Session = Depends(get_db)):
    try:
        token = request.token  # Extract token from JSON body
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token["email"]

        # Check if user exists
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            new_user = User(id=uid, email=email, name=decoded_token.get("name", ""))
            db.add(new_user)
            db.commit()
            return {"message": "New user created", "email": new_user.email}

        return {"message": "User already exists", "email": user.email}
    except Exception as e:
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
