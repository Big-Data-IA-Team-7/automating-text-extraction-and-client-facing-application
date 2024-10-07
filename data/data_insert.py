# This Python script provides functions to connect to a MySQL database and fetch data into pandas DataFrames.
# It includes a function to retrieve data from the 'gaia_metadata_tbl' table, utilizing a separate database 
# connection module. The script handles database connections, data retrieval, and logs the process using a 
# logging module, ensuring that data fetching operations are monitored and recorded for debugging and auditing purposes.

import mysql.connector
import pandas as pd
from data.db_connection import get_db_connection
from data.data_read import close_my_sql_connection
from datetime import datetime
from project_logging import logging_module

def insert_user(username: str, password: str):
    """
    Inserts a new user into the 'users_tbl' table in the MySQL database.

    Args:
        username (str): The username of the new user.
        password (str): The password of the new user.

    Raises:
        ValueError: If the username already exists.
    """
    try:
        # Connect to MySQL database
        mydb = get_db_connection()
        
        if mydb.is_connected():
            logging_module.log_success("Connected to the database for inserting user data.")

            # Create a cursor object
            cursor = mydb.cursor()

            # Insert user into the database
            cursor.execute("INSERT INTO users_tbl (username, hashed_password) VALUES (%s, %s)", (username, password))
            mydb.commit()

            logging_module.log_success(f"User {username} registered successfully.")

    except mysql.connector.Error as e:
        # Handle duplicate username error
        if e.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
            raise ValueError("Username already exists.")
        logging_module.log_error(f"Database error occurred during user insertion: {e}")

    except Exception as e:
        logging_module.log_error(f"An unexpected error occurred during user insertion: {e}")

    finally:
        # Ensure that the cursor and connection are properly closed
        close_my_sql_connection(mydb)
