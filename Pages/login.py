import streamlit as st
import requests
from dotenv import load_dotenv
load_dotenv()
import os


# Define the FastAPI URL for login
LOGIN_API_URL = os.getenv('LOGIN_API_URL')

# Function for the login page
def login():
    st.title("Login Page")
    
    # Initialize session state for login status if it doesn't exist
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Create a form for user input
    with st.form(key='login_form'):
        username = st.text_input("Enter the Username")
        password = st.text_input("Enter the Password", type='password')
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            # Send a POST request to the FastAPI login endpoint
            response = requests.post(LOGIN_API_URL, data={"username": username, "password": password})
            
            if response.status_code == 200:
                st.success("Login successful!")
                st.session_state.logged_in = True  # Update login status
                st.session_state.username=username
                st.session_state.page = 'login_user'  # Set the page to user login
                st.rerun()  # Rerun the script to refresh the page
            elif response.status_code == 401:
                st.error("Invalid credentials. Please try again.")
            else:
                st.error("An error occurred while trying to log in.")

    # Navigation to Register Page
    if st.button("Register"):
        st.session_state.page = 'register'  # Switch to register page
        st.rerun()  # Rerun the script to refresh the page
