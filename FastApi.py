from fastapi import FastAPI, HTTPException, Form
from data.data_read import fetch_data_from_db
from data.data_insert import insert_user 
from typing import List
import pandas as pd

# Create FastAPI instance
app = FastAPI()

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

@app.post("/login/")
async def login(username: str = Form(...), password: str = Form(...)):
    print(f"Received username: {username}, password: {password}")  # Debugging output
    try:
        user_data = fetch_data_from_db()  # Assuming this fetches a DataFrame with user info
        print(user_data)
        if isinstance(user_data, pd.DataFrame):
            user_row = user_data[user_data['name'] == username]
            if not user_row.empty and user_row['password'].values[0] == password:
                return {"status": "success"}
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch user data from database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register/")
async def register(username: str = Form(...), password: str = Form(...)):
    print(f"Received username: {username}, password: {password}")  # Debugging output
    try:
        user_data = fetch_data_from_db()
        if isinstance(user_data, pd.DataFrame):
            if username in user_data['name'].values:
                raise HTTPException(status_code=400, detail="Username already exists")
            insert_user(username, password)  # Ensure this function is correct
            return {"status": "success", "message": "User registered successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch user data from database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))