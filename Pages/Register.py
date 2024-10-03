import streamlit as st
import requests
from dotenv import load_dotenv
load_dotenv()
import os

# Define the FastAPI URL for registration
REGISTER_API_URL = os.getenv('REGISTER_API_URL')

# Function for the registration page
def register():
    st.title("Register Page")

    # Create a form for user input
    with st.form(key='register_form'):
        new_username = st.text_input("Enter the Username")
        new_password = st.text_input("Enter the Password", type='password')
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            # Send a POST request to the FastAPI registration endpoint
            response = requests.post(REGISTER_API_URL, data={"username": new_username, "password": new_password})

            # Check the response
            if response.status_code == 200:
                st.success("Registration successful!")
                # Optionally, redirect or perform additional actions after successful registration
            elif response.status_code == 400:
                st.error("Username already exists.")
            else:
                st.error("An error occurred during registration.")
                st.write(f"Response Content: {response.text}")  # Print response for debugging

            
    # Navigation to Login Page
    if st.button("Go to Login"):
        st.session_state.page = 'login'  # Switch back to login page
