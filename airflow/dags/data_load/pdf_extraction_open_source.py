import pymupdf4llm
import os
import boto3
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
from data_load.db_connection import get_db_connection
from io import BytesIO
import tempfile


load_dotenv()

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')


def process_pdf_open_source():
    # MySQL connection
    db_conn = get_db_connection()
    
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    
    response = s3_client.list_objects_v2(Bucket=aws_bucket_name, Prefix='gaia_files/')
    open_source_output_folder = 'open_source_processed/'
    
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.pdf'):
            # Read the PDF file from S3
            pdf_obj = s3_client.get_object(Bucket=aws_bucket_name, Key=obj['Key'])
            pdf_data = pdf_obj['Body'].read()
    
            # Use a temporary file if needed
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                temp_file.write(pdf_data)
                temp_file.flush()  # Ensure data is written
    
                # Convert PDF to markdown text using the temp file's name
                md_text = pymupdf4llm.to_markdown(temp_file.name, embed_images=True, table_strategy='lines')
    
            # Define output file name and path
            output_key = open_source_output_folder + obj['Key'].split('/')[-1].replace('.pdf', '.txt')
    
            # Upload the markdown text to the output S3 directory as a .txt file
            s3_client.put_object(Bucket=aws_bucket_name, Key=output_key, Body=md_text)
    
            print(f"Processed and uploaded: {output_key}")
    