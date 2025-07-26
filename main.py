from fastapi import FastAPI,HTTPException,Depends,Request,BackgroundTasks,status
from fastapi.responses import JSONResponse,HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime  



from Assessment.main import Assess
from accessories.exception import CustomException
from llm_setup.main import LLMSetup
from pydantic import BaseModel
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict,List
import os
import json
import sys


#imports that may be shifted
from accessories.utils import load_json
from accessories.logger import logging
from core_logic.data_related.schemas import TestRequest,TestAndAnswer,solRequest,TokenRequest,TextInput,TokenRequestRegister,UserCreate ,UserResponse,Token, UserInfo, TestHistoryResponse
from Assessment.test_inference import get_inference


# Database imports 
from core_logic.data_related.database import User, Base, engine, SessionLocal, TestHistory
from sqlalchemy.orm import Session 
from sqlalchemy.exc import SQLAlchemyError


#chatbot imports
from ChatBot.main import Chatbot
import re


# <----------------------------------------------------------------Authentication--------------------------------------------------->
# Imports for registration and login using jwt tokens 
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
# <--------------------------------------------------------------------------------------------------------------------------------->



load_dotenv()
app = FastAPI(title  = "Miraat")
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
BASE_URL = os.getenv("BASE_URL")



# <---------------------------------------------------------------- SECRET KEY ----------------------------------------------------->
# Secret key for JWT signing
SECRET_KEY = os.getenv("SECRET_KEY")
os.environ["SECRET_KEY"] = SECRET_KEY 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# <--------------------------------------------------------------------------------------------------------------------------------->






# TODO: To be shifted in utilities 
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)








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


@app.get("/chatbot")
async def assessment(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})







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


# ---------------------------------------------------------Storing the test in the database-------------------------------------------------------------- 


def store(user_name: str, userinput: str, response: str, db: Session):
    try:
        new_entry = TestHistory(
            user_name=user_name,
            userinput=userinput,
            response=response
        )
        
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        print(f"Stored entry ID: {new_entry.test_id}")  # Verify ID generation
        logging.info(f"Stored entry ID: {new_entry.test_id}")  # Verify ID generation
        return new_entry
        
    except Exception as e:
        logging.error(f"Storage error: {str(e)}", exc_info=True)
        db.rollback()
        raise

# -------------------------------------------------------------------------------------------------------------------------------------------------------
    
@app.post("/get_solution_text/")
async def get_solution_text(texti: solRequest, db: Session = Depends(get_db)):
    
    print(texti.dict())

    text = texti.context
    name = texti.username
    age = texti.age
    gender = texti.gender 
    
    logging.info(text)

    

    try:
        set_up = LLMSetup()
        solution_html = set_up.get_result(text, name, age, gender)
        logging.info(f"Generated solution: {solution_html}")

        try:
            store(name, text, solution_html,db)
        except Exception as store_error:
            # Handle storage failure specifically
            logging.error(f"Storage failed: {store_error}", exc_info=True)
            # Consider adding retry logic here

        return JSONResponse(
            content={"solution_text": solution_html}
        )

    except Exception as main_error:
        logging.critical(f"Main process failed: {main_error}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(main_error)}")






# <----------------------------------------------------------------------- Helpline --------------------------------------------------------------------------->
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
# <------------------------------------------------------------------------------------------------------------------------------------------------------------->
        





#<----------------------------------------------------------- Login related utility funtions --------------------------------------------------------------------> 
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.name == username).first()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user: UserCreate):
    # Hash the password before storing
    hashed_password = pwd_context.hash(user.hashed_password)
    
    db_user = User(
        name=user.name,
        age=user.age,
        gender = user.gender,
        email=user.email,
        hashed_password=hashed_password  # Use the hashed password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user





def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt





# User authentication 

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user





# <---------------------------------------------------------- login system ---------------------------------------------------------------------------------------->



@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})






@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    existing_user = get_user_by_username(db, user.name)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # Create new user
    created_user = create_user(db, user)
    
    # Return response matching UserResponse model
    return {
        "name": created_user.name,  # Add this line
        "email": created_user.email,
        "message": "User registered successfully"
    }






@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)  # Use username instead of name
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.name})
    return {"access_token": access_token,"username":user.name,"age":user.age,"gender":user.gender,"token_type": "bearer"}







# Not being used. 
@app.get("/dashboard")
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    if current_user is None:
        # Redirect to login page if the user is not authenticated
        return RedirectResponse(url="/login", status_code=302)
    
    # If authenticated, render the dashboard
    return templates.TemplateResponse("assessment.html", {
        "request": request,
        "username": current_user.name
    })



    # <--------------------------------------------------------------  Chatbot Related endpoints and functions -------------------------------------------------------------------------------->


chatbot  = None

def initialize_chatbot(name:str,age,gender):
    """Initialize the chatbot instance."""
    # Create a new chatbot instanc

    global chatbot
    chatbot = Chatbot(name,age,gender)
    return chatbot



def format_msg(input_text):
    # Replace double asterisks for bold text
    formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', input_text)

    # Replace single asterisks for italic text
    formatted_text = re.sub(r'(?<!\*)\*(.*?)\*(?!\*)', r'<i>\1</i>', formatted_text)

    # Format list items (new line for each list item)
    formatted_text = re.sub(r'(\d+\.\s)', r'<br>\1', formatted_text)  # For numbered lists
    formatted_text = re.sub(r'(\*\s)', r'<br>\1', formatted_text)      # For bullet points

    return formatted_text


# --------------------------------------------------------------------------- Endpoints ---------------------------------------------------------------------------------------------------------
@app.post("/start_chatbot_session")
async def start_chatbot_session(info: UserInfo):
    name = info.name
    age = info.age
    gender = info.gender
    chatbot = initialize_chatbot(name,age,gender)
    return JSONResponse(content={"name": name})

 
@app.post("/chatbot_response")
async def chatbot_response(msg:TextInput):
    temp  = format_msg(chatbot.chat(msg.text))
    return JSONResponse(content={"response": temp})







# <----------------------------------------------------------------------------  History Section ------------------------------------------------------------------------------------------------------------------->


@app.get("/history")
async def assessment(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})



@app.get("/test-history", response_model=List[TestHistoryResponse])
def get_test_history(user_name: str, db: Session = Depends(get_db)):
    # Fetch test history for the given username
    test_history = db.query(TestHistory).filter(TestHistory.user_name == user_name).order_by(TestHistory.date.desc()).all()
    if not test_history:
        raise HTTPException(status_code=404, detail="No test history found")
    return test_history
 

#  <----------------------------------------------------------------------------------------------------------------------  Community Section  ---------------------------------------------------------------------------------------->
