# This Python script provides functions to connect to a MySQL database and fetch data into pandas DataFrames.
# It includes a function to retrieve data from the 'userlogin' table, utilizing a separate database 
# connection module. The script handles database connections, data retrieval, and logs the process using a 
# logging module, ensuring that data fetching operations are monitored and recorded for debugging and auditing purposes.

import mysql.connector
import pandas as pd
from data.db_connection import get_db_connection
from datetime import datetime
from project_logging import logging_module

def fetch_user_from_db(username: str) -> pd.DataFrame:
    """
    Fetches username from the 'users_tbl' table in the MySQL database and returns the username.

    Returns:
        pd.DataFrame: A DataFrame containing the username and password fetched from the database, or None if an error occurs.
    """
    try:
        # Connect to MySQL database
        mydb = get_db_connection()
        
        if mydb.is_connected():
            logging_module.log_success("Connected to the database for fetching data.")

            # Create a cursor object
            mydata = mydb.cursor()

            # Execute the query
            mydata.execute("SELECT username, hashed_password FROM users_tbl WHERE username = %s", (username,))
            
            # Fetch only the username
            user_data = mydata.fetchall()

            logging_module.log_success("Fetched data from users_tbl")

            # Get column names
            columns = [col[0] for col in mydata.description]

            if user_data:
                # Store the fetched data into a pandas DataFrame
                user_df = pd.DataFrame(user_data, columns=columns)
                return user_df
            else:
                logging_module.log_success("No user found with the provided username.")
                return None

    except mysql.connector.Error as e:
        logging_module.log_error(f"Database error occurred: {e}")
        return None

    except Exception as e:
        logging_module.log_error(f"An unexpected error occurred: {e}")
        return None

    finally:
        # Ensure that the cursor and connection are properly closed
        close_my_sql_connection(mydb, mydata)

#Fetching the data for 'Gaia_metadata_tbl_pdf'
def fetch_data_from_db() -> pd.DataFrame:
    """
    Fetches data from the 'user login' table in the MySQL database and returns it as a pandas DataFrame.

    Returns:
        pd.DataFrame: A DataFrame containing the data fetched from the database, or None if an error occurs.
    """
    try:
        # Connect to MySQL database
        mydb = get_db_connection()
        
        if mydb.is_connected():
            logging_module.log_success("Connected to the database for fetching data.")

            # Create a cursor object
            mydata = mydb.cursor()

            # Execute the query
            mydata.execute("SELECT * FROM gaia_metadata_tbl_pdf")
            
            # Fetch all the data
            myresult = mydata.fetchall()

            logging_module.log_success("Fetched data from gaia_metadata_tbl_pdf")

            # Get column names
            columns = [col[0] for col in mydata.description]

            # Store the fetched data into a pandas DataFrame
            df = pd.DataFrame(myresult, columns=columns)

            return df

    except mysql.connector.Error as e:
        logging_module.log_error(f"Database error occurred: {e}")
        return None

    except Exception as e:
        logging_module.log_error(f"An unexpected error occurred: {e}")
        return None

    finally:
        # Ensure that the cursor and connection are properly closed
        close_my_sql_connection(mydb, mydata)


def close_my_sql_connection(mydb, mydata = None):
    try:
        if mydb.is_connected():
            mydata.close()
            mydb.close()
            logging_module.log_success("MySQL connection closed.")
    except Exception as e:
        logging_module.log_error(f"Error closing the MySQL connection: {e}")