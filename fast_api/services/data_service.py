import mysql.connector
import pandas as pd
from fast_api.config.db_connection import close_my_sql_connection, get_db_connection
from project_logging import logging_module
import boto3
from urllib.parse import urlparse, unquote
import os
import requests
import tempfile
from project_logging import logging_module
import pandas as pd
from parameter_config import ACCESS_KEY_ID_AWS, SECRET_ACCESS_KEY_AWS

# Initialize S3 client
s3 = boto3.client('s3',
                  aws_access_key_id=ACCESS_KEY_ID_AWS,
                  aws_secret_access_key=SECRET_ACCESS_KEY_AWS)

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

def parse_s3_url(url: str) -> tuple:
    """
    Parses an S3 URL to extract the bucket name and object key.

    Args:
        url (str): The S3 URL to be parsed.

    Returns:
        tuple: A tuple containing the bucket name (str) and the object key (str).
    """
    parsed_url = urlparse(url)
    bucket_name = parsed_url.netloc.split('.')[0]  # Extract bucket name
    object_key = parsed_url.path.lstrip('/')       # Extract object key
    return bucket_name, object_key

def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Generates a pre-signed URL for an S3 object that allows temporary access.

    Args:
        s3_url (str): The S3 URL of the object (e.g., 'https://bucket-name.s3.amazonaws.com/object-key').
        expiration (int, optional): The time in seconds until the pre-signed URL expires. Defaults to 3600 seconds (1 hour).

    Returns:
        str: The pre-signed URL allowing temporary access to the S3 object, or None if an error occurs.
    """
    bucket_name, object_key = parse_s3_url(s3_url)
    
    try:
        # Generate pre-signed URL that expires in the given time (default: 1 hour)
        presigned_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': bucket_name, 'Key': object_key},
                                                  ExpiresIn=expiration)
        return presigned_url
    except Exception as e:
        logging_module.log_error(f"Error generating pre-signed URL: {e}")
        return None

def process_data_and_generate_url(question: str, df, extraction_method: str = None) -> str:
    """
    Fetches data from the database, extracts the S3 URL for the specified question, and generates a pre-signed URL if available.

    Args:
        question (str): The question for which the associated S3 URL needs to be retrieved.

    Returns:
        str: A pre-signed URL for the S3 file if available.
    """
    if df is not None:
        # Extract the S3 URL for the specified Question
        matching_rows = df[df['Question'] == question]
        if not matching_rows.empty:
            if extraction_method == 'U':
                s3_url_variable = matching_rows['unstructured_api_url'].values[0]
                print("S3 URL: ", s3_url_variable)
                logging_module.log_success(f"Unstructured S3 URL: {s3_url_variable}")
            elif extraction_method == 'P':
                s3_url_variable = matching_rows['opensource_url'].values[0]
                logging_module.log_success(f"PyMuPDF S3 URL: {s3_url_variable}")
            else:
                s3_url_variable = matching_rows['s3_url'].values[0]
                logging_module.log_success(f"S3 URL: {s3_url_variable}")

            # Check if s3_url_variable is null
            if s3_url_variable is not None:
                # Generate a pre-signed URL for the S3 file
                presigned_url = generate_presigned_url(s3_url_variable, expiration=3600)  # URL valid for 1 hour
                return presigned_url
            else:
                logging_module.log_success("No File is associated with this Question")
                return None
        else:
            logging_module.log_error("No matching Question found")
            return None
    else:
        logging_module.log_error("Failed to fetch data from the database")
        return None
 
def download_file(question: str, df: pd.DataFrame, extraction_method: str = None) -> dict:
    """
    Downloads a file from the given URL and saves it as a temporary file with the appropriate extension.

    Args:
        url (str): The URL of the file to be downloaded.

    Returns:
        dict: A dictionary containing the following keys:
            - "url" (str): The original URL of the file.
            - "path" (str): The path to the downloaded temporary file.
            - "extension" (str): The file extension of the downloaded file.
    """
    # Parse the URL to extract the file name
    file_name = process_data_and_generate_url(question, df, extraction_method)
    parsed_url = urlparse(file_name)
    path = unquote(parsed_url.path)
    filename = os.path.basename(path)
    extension = os.path.splitext(filename)[1]

    # Create a temporary directory to hold the file
    temp_dir = "/code/temp_files"
    os.makedirs(temp_dir, exist_ok=True)

    # Create a temporary file in the specified directory
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=extension, dir=temp_dir)

    # Get the file from the URL
    response = requests.get(file_name)
    response.raise_for_status()  # Check if the download was successful

    # Write the content to the temporary file
    temp.write(response.content)
    temp.close()  # Close the file to finalize writing
    
    return {"url": file_name, "path": temp.name, "extension": extension}