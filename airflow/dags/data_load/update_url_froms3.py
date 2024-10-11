# This script fetches file URLs from an AWS S3 bucket and updates a metadata table in MySQL RDS.

# It connects to AWS S3 using `boto3` to list objects under a specified prefix (folder path).
# Extracts file names, removes ".json" extensions, and converts ".txt" extensions to ".pdf" for metadata consistency.
# Establishes a connection to an AWS RDS MySQL instance using a custom `get_db_connection` function.
# Updates either the `unstructured_api_url` or `opensource_url` column in the MySQL table based on the file prefix.
# Includes exception handling for S3 and MySQL interactions to ensure robust error management and proper logging.
# Closes the MySQL connection gracefully after updating the metadata, ensuring the database is updated successfully.


import os
import re
import boto3
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from data_load.db_connection import get_db_connection
from data_load.parameter_config_airflow import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME

# Function to fetch all file URLs from S3 and update metadata table in MySQL RDS
def update_metadata_with_s3_urls(prefix):
    """
    This function retrieves file URLs from an S3 bucket and updates the relevant metadata in an AWS RDS MySQL table.
    It processes files under the specified prefix and updates either the 'unstructured_api_url' or 'opensource_url' column.
    
    Args:
        prefix (str): The S3 directory (prefix) to search for files.
    """
    
    # AWS S3 credentials
    aws_access_key_id = AWS_ACCESS_KEY_ID
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    aws_bucket_name = AWS_S3_BUCKET_NAME

    # Initialize S3 client
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        print("Connected to S3 successfully.")
    except Exception as e:
        print(f"Error initializing S3 client: {e}")
        return

    # Fetch all file URLs from the S3 directory
    try:
        response = s3.list_objects_v2(Bucket=aws_bucket_name, Prefix=prefix)
    except Exception as e:
        print(f"Error fetching objects from S3: {e}")
        return

    # If no files are found
    if 'Contents' not in response:
        print("No files found in the given S3 directory.")
        return

    # Extract URLs and clean up file names
    file_urls = []
    file_names = []
    try:
        for obj in response['Contents']:
            file_key = obj['Key']
            file_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{file_key}"
            file_name_with_extension = file_key.split('/')[-1]
            # Replace ".json" with "" and ".txt" with ".pdf"
            file_name = re.sub(r'\.json$', '', file_name_with_extension)
            file_name = re.sub(r'\.txt$', '.pdf', file_name)

            file_names.append(file_name)
            file_urls.append(file_url)
        print("File URLs and names processed successfully.")
    except Exception as e:
        print(f"Error processing file URLs and names: {e}")
        return

    # Update MySQL table with URLs
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for url, file_name in zip(file_urls, file_names):
            print(f"Updating file: {file_name} with URL: {url}")
        
            # Determine which column to update based on the prefix
            if prefix == 'unstructured_extract/':
                update_query = """
                UPDATE gaia_metadata_tbl_pdf
                SET unstructured_api_url = %s
                WHERE file_name = %s
                """
            else:
                update_query = """
                UPDATE gaia_metadata_tbl_pdf
                SET opensource_url = %s
                WHERE file_name = %s
                """
            
            # Execute the update query
            cursor.execute(update_query, (url, file_name))
    
        # Commit changes to the database
        conn.commit()
        print("Metadata table updated successfully.")
    except mysql.connector.Error as e:
        print(f"Error updating RDS table: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed after updating metadata.")
