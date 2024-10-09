import streamlit as st
import requests
from parameter_config import FAST_API_DEV_URL

# Function for the registration page
def register():
    st.title("PDF Extractor Tool :page_with_curl:")
    st.header("Register")

    # Create a form for user input
    with st.form(key='register_form'):
        first_name = st.text_input("**Enter Your First Name**")
        new_username = st.text_input("**Create Your Username**")
        new_password = st.text_input("**Create Your Password**", type='password')
        submit_button = st.form_submit_button("Register")
        
        if submit_button:

            payload = {
                "username": new_username,
                "password": new_password,
                "first_name": first_name
            }
            # Send a POST request to the FastAPI registration endpoint
            response = requests.post(f"{FAST_API_DEV_URL}/auth/register/", json=payload)

            # Check the response
            if response.status_code == 200:
                st.success("Registration successful!")
                # Optionally, redirect or perform additional actions after successful registration
            elif response.status_code == 400:
                st.error("Username already exists.")
            else:
                st.error("An error occurred during registration.")
                st.write(f"Response Content: {response.text}")  # Print response for debugging
