# This script processes PDF files stored in an AWS S3 bucket by converting them to markdown text.
# It connects to AWS S3 to read PDF files from a specific folder, processes them using the pymupdf4llm library,
# and converts them to markdown format with embedded images and tables.
# The processed markdown files are then uploaded back to the S3 bucket in a specified output folder as .txt files.
# The script uses a temporary file to handle the PDF data during processing, ensuring efficient file management.
# It also logs each successful upload after processing.

import pymupdf4llm
import os
import boto3
import pandas as pd
import mysql.connector
from data_load.db_connection import get_db_connection
from io import BytesIO
from data_load.parameter_config_airflow import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Getting AWS credentials from environment variables
aws_access_key_id = AWS_ACCESS_KEY_ID
aws_secret_access_key = AWS_SECRET_ACCESS_KEY
aws_bucket_name = AWS_S3_BUCKET_NAME

def process_pdf_open_source():
    """
    This function processes PDF files from an S3 bucket by converting them to markdown text and uploading the
    converted text files back to the S3 bucket. Uses pymupdf4llm for conversion, and handles PDFs using a temporary file.
    """
    # MySQL connection (not used in the processing but available for future use)
    try:
        db_conn = get_db_connection()
        logging.info("MySQL connection established successfully.")
    except mysql.connector.Error as e:
        logging.error(f"Error connecting to MySQL: {e}")
        return

    # S3 client setup
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        logging.info("Connected to S3 successfully.")
    except Exception as e:
        logging.error(f"Error setting up S3 client: {e}")
        return
    
    try:
        # List PDF files in the specified S3 directory
        response = s3_client.list_objects_v2(Bucket=aws_bucket_name, Prefix='gaia_files/')
        open_source_output_folder = 'open_source_processed/'
    except Exception as e:
        logging.error(f"Error listing objects in S3 bucket: {e}")
        return

    # Process each PDF file in the list
    for obj in response.get('Contents', []):
        if obj['Key'].endswith('.pdf'):
            try:
                # Read the PDF file from S3
                pdf_obj = s3_client.get_object(Bucket=aws_bucket_name, Key=obj['Key'])
                pdf_data = pdf_obj['Body'].read()
                logging.info(f"Downloaded PDF: {obj['Key']}")
            except Exception as e:
                logging.error(f"Error reading PDF from S3: {obj['Key']}, {e}")
                continue

            try:
                # Use a temporary file to store the PDF data for processing
                with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                    temp_file.write(pdf_data)
                    temp_file.flush()  # Ensure data is written to the temp file

                    # Convert PDF to markdown text using pymupdf4llm
                    md_text = pymupdf4llm.to_markdown(temp_file.name, embed_images=True, table_strategy='lines')
                    logging.info(f"Converted PDF to markdown: {obj['Key']}")
            except Exception as e:
                logging.error(f"Error processing PDF to markdown: {obj['Key']}, {e}")
                continue

            try:
                # Define output file name and path for uploading the markdown text as a .txt file
                output_key = open_source_output_folder + obj['Key'].split('/')[-1].replace('.pdf', '.txt')

                # Upload the markdown text to S3 as a .txt file
                s3_client.put_object(Bucket=aws_bucket_name, Key=output_key, Body=md_text)
                logging.info(f"Uploaded markdown file to S3: {output_key}")
            except Exception as e:
                logging.error(f"Error uploading markdown file to S3: {output_key}, {e}")
                continue

    logging.info("Processing completed.")
