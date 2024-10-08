import os
import re
import boto3
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from data_load.db_connection import get_db_connection

# Load environment variables
load_dotenv()


# Function to fetch all file URLs from S3 and update metadata table in MySQL RDS
def update_metadata_with_s3_urls(prefix):
    # AWS S3 credentials
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

    # Initialize S3 client
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    # Fetch all file URLs from the S3 directory
    response = s3.list_objects_v2(Bucket=aws_bucket_name, Prefix=prefix)

    # If no files are found
    if 'Contents' not in response:
        print("No files found in the given S3 directory.")
        return

    # Extract URLs and remove ".json" extension
    file_urls = []
    file_names = []
    for obj in response['Contents']:
        file_key = obj['Key']
        file_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{file_key}"
        file_name_with_extension = file_key.split('/')[-1]
        # Replace ".json" with "" and ".txt" with ".pdf"
        file_name = re.sub(r'\.json$', '', file_name_with_extension)
        file_name = re.sub(r'\.txt$', '.pdf', file_name)

        file_names.append(file_name)
        file_urls.append(file_url)

    # Update MySQL table with URLs
    conn = get_db_connection()
    try:
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

            # Execute the appropriate query
            cursor.execute(update_query, (url, file_name))
    
        # Commit changes to the database
        conn.commit()
        print("Metadata table updated successfully.")
    except Exception as e:
        print(f"Error updating RDS table: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("MySQL connection closed after updating metadata.")



#update_metadata_with_s3_urls(prefix)
