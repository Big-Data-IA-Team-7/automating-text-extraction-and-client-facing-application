from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from data.data_read import fetch_data_from_db, fetch_user_from_db
from data.data_insert import insert_user
from data.data_s3 import download_file
from typing import List, Dict
import pandas as pd

import os
import base64
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta, timezone
import hmac, hashlib, jwt
from project_logging import logging_module
from pydantic import BaseModel, Field
from openai_api.openai_api_call import OpenAIClient

# Define a Pydantic model for the request body
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="The user's unique username")
    password: str = Field(..., min_length=6, description="The user's password, must be at least 6 characters")

class RegisterUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="The user's unique username")
    password: str = Field(..., min_length=6, description="The user's password, must be at least 6 characters")
    first_name: str = Field(None, max_length=50, description="First name of the user (optional)")
    last_name: str = Field(None, max_length=50, description="Last name of the user (optional)")
    email: str = Field(None, max_length=50, description="Email of the user (optional)")

class DownloadRequest(BaseModel):
    question: str
    df: List[Dict]

class OpenAIRequest(BaseModel):
    model: str = Field(..., min_length=3, max_length=15, description="The model to send the request to")
    question_selected: str = Field(..., description="The question selected by the user")
    annotated_steps: str = Field(None, description="The annotated steps if any for the question (optional)")

# Create FastAPI instance
app = FastAPI()
security = HTTPBearer()

encoded_key = os.getenv('SECRET_KEY')

def hash_password(password: str) -> str:
    secret_key = base64.b64decode(encoded_key)
    hash_object = hmac.new(secret_key, msg=password.encode(), digestmod=hashlib.sha256)
    hash_hex = hash_object.hexdigest()
    return hash_hex

def create_jwt_token(data: dict):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=50)
    token_payload = {"exp": expiration, **data}
    token = jwt.encode(token_payload, encoded_key, algorithm='HS256')
    return token, expiration

def decode_jwt_token(token: str):
    try:
        decoded_token = jwt.decode(token, encoded_key, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired',
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    token = authorization.credentials
    try:
        payload = decode_jwt_token(token)
        username = payload.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token payload',
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = fetch_user_from_db(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found',
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.to_dict(orient="records")[0]
    except HTTPException as e:
        logging_module.log_error(f"An unexpected error occurred: {e}")
        return e

@app.post("/login/")
def login(request: LoginRequest):
    username = request.username
    password = request.password
    user = fetch_user_from_db(username)
    print(user["username"])
    print(user["hashed_password"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found.',
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.iloc[0]["username"] and user.iloc[0]["hashed_password"] == hash_password(password):
        token, expiration = create_jwt_token({"username": username})
        return {"access_token": token, "token_type": "bearer", "expires": expiration.isoformat()}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password.',
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/register/")
def register(request: RegisterUserRequest):
    username = request.username
    password = request.password
    first_name = request.first_name
    last_name = request.last_name
    email = request.email
    user = fetch_user_from_db(username)
    if user is None:
        # Insert the user with the hashed password into the database
        insert_user(username, hash_password(password))  # Ensure this function inserts hashed password
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already exists.',
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/fetch-questions/", response_model=List[dict])
def get_questions_for_user(current_user: Dict = Depends(get_current_user)):

    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is fetching data from the database.")

    # Fetch data from the database
    data = fetch_data_from_db()

    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient="records")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No data returned from the database",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/fetch-download-url/", response_model=Dict)
def get_download_url(request: DownloadRequest, current_user: Dict = Depends(get_current_user)):

    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is fetching data from the database.")

        # Convert the request df back to a DataFrame
    df = pd.DataFrame(request.df)
    question = request.question

    download_url = download_file(question, df)
                  
    return download_url

@app.get("/fetch-openai-response/", response_model=str)
def get_openai_response(request: OpenAIRequest, current_user: Dict = Depends(get_current_user)):
    
    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is fetching data from the database.")

    question_selected = request.question_selected
    model = request.model
    annotated_steps = request.annotated_steps
    
    client = OpenAIClient()

    response = client.validation_prompt(question_selected, model, annotated_steps)

    return response