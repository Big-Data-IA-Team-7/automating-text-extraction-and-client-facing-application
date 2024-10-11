# This Python script establishes a connection to an AWS RDS MySQL database using environment variables for 
# credentials and connection details. It securely loads these variables using the `dotenv` package and 
# defines a function `get_db_connection()` to create and return a connection object, facilitating database 
# interactions within the application.

import os
import mysql.connector
from project_logging import logging_module
from parameter_config import RDS_HOST_AWS, RDS_USERNAME_AWS, RDS_PASSWORD_AWS, RDS_DATABASE_AWS, RDS_DB_PORT_AWS

def get_db_connection() -> mysql.connector.connection_cext.CMySQLConnection:
    """
    Establishes and returns a connection to the AWS RDS MySQL database using the provided credentials.

    Returns:
        mysql.connector.connection_cext.CMySQLConnection: A MySQL database connection object.
    """
    return mysql.connector.connect(
        host= RDS_HOST_AWS,
        user=RDS_USERNAME_AWS,
        password=RDS_PASSWORD_AWS,
        port =RDS_DB_PORT_AWS,
        database=RDS_DATABASE_AWS
    )

def close_my_sql_connection(mydb, mydata = None):
    try:
        if mydb.is_connected():
            mydata.close()
            mydb.close()
            logging_module.log_success("MySQL connection closed.")
    except Exception as e:
        logging_module.log_error(f"Error closing the MySQL connection: {e}")