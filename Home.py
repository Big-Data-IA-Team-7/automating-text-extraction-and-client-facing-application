import streamlit as st
import requests

# Define the FastAPI URLs
LOGIN_API_URL = "http://127.0.0.1:8000/login/"
REGISTER_API_URL = "http://127.0.0.1:8000/register/"

# Function for the login page

def login():
    st.title("Login Page")

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
                # Optionally, redirect or perform additional actions after a successful login
            elif response.status_code == 401:
                st.error("Invalid credentials. Please try again.")
            else:
                st.error("An error occurred while trying to log in.")

    # Navigation to Register Page
    if st.button("Register"):
        st.session_state.page = 'register'  # Switch to register page

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

# Initialize session state for page tracking
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Display the appropriate page based on the session state
if st.session_state.page == 'login':
    login()
else:
    register()
