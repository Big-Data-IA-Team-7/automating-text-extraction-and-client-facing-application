from fastapi import FastAPI, HTTPException, Form
from passlib.hash import pbkdf2_sha256
from data.data_read import fetch_user_data_from_db, fetch_data_from_db
from data.data_insert import insert_user
from typing import List
import pandas as pd

# Create FastAPI instance
app = FastAPI()

# Hash password
def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)

# Verify password
def verify_password(password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed_password)

# Define a route to fetch data
@app.get("/fetch-data/", response_model=List[dict])
def get_data():
    try:
        # Fetch data from the database
        data = fetch_data_from_db()
        if isinstance(data, pd.DataFrame):
            return data.to_dict(orient="records")
        else:
            raise HTTPException(status_code=500, detail="No data returned from the database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Login route
@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    print(f"Received username: {username}, password: {password}")  # Debugging output
    try:
        user_data = fetch_user_data_from_db()  # Assuming this fetches a DataFrame with user info
        if isinstance(user_data, pd.DataFrame):
            user_row = user_data[user_data['name'] == username]
            if not user_row.empty:
                # Verify the password using the hashed password stored in the DB
                stored_hashed_password = user_row['password'].values[0]
                if verify_password(password, stored_hashed_password):
                    return {"status": "success", "message": "Logged in successfully"}
                else:
                    raise HTTPException(status_code=401, detail="Invalid credentials")
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch user data from database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Register route
@app.post("/register/")
async def register(username: str = Form(...), password: str = Form(...)):
    print(f"Received username: {username}, password: {password}")  # Debugging output
    try:
        user_data = fetch_user_data_from_db()
        if isinstance(user_data, pd.DataFrame):
            if username in user_data['name'].values:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Hashing the password before storing it
            hashed_password = hash_password(password)
            
            # Insert the user with the hashed password into the database
            insert_user(username, hashed_password)  # Ensure this function inserts hashed password
            return {"status": "success", "message": "User registered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch user data from database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
