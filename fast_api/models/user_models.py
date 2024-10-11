import mysql.connector
import pandas as pd
from fast_api.config.db_connection import close_my_sql_connection, get_db_connection
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
            mydata.execute("SELECT first_name, username, hashed_password FROM users_tbl WHERE username = %s", (username,))
            
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

def insert_user(first_name: str, username: str, password: str):
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
            cursor.execute("INSERT INTO users_tbl (first_name, username, hashed_password) VALUES (%s, %s, %s)", (first_name, username, password))
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