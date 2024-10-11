'''This script automates the process of loading GAIA metadata into AWS RDS MySQL and uploading files to AWS S3.
It connects to Hugging Face to fetch the GAIA dataset, processes it, and inserts the metadata into MySQL.
Files are downloaded from Hugging Face, uploaded to S3, and the MySQL table is updated with S3 URLs and file extensions.
Error handling is included for database connections, API requests, and file operations, ensuring smooth execution.
The script is designed to handle large datasets efficiently while logging success and failure at each step.
'''

import os
from datasets import load_dataset
from huggingface_hub import login
import json
import boto3
import requests
import mysql.connector
from mysql.connector import Error
from data_load.parameter_config_airflow import AWS_ACCESS_KEY_ID , AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME, AWS_RDS_HOST, AWS_RDS_USERNAME, AWS_RDS_PASSWORD, AWS_RDS_DB_PORT, AWS_RDS_DATABASE, HUGGINGFACE_TOKEN
import data_load.data_storage_log as logging_module
from data_load.db_connection import get_db_connection
import pandas as pd
import logging
import data_load.parameter_config_airflow

# Getting environmental variables
aws_access_key_id = AWS_ACCESS_KEY_ID
aws_secret_access_key = AWS_SECRET_ACCESS_KEY
aws_bucket_name = AWS_S3_BUCKET_NAME
aws_rds_host = AWS_RDS_HOST
aws_rds_user = AWS_RDS_USERNAME
aws_rds_password = AWS_RDS_PASSWORD
aws_rds_port = AWS_RDS_DB_PORT
aws_rds_database = AWS_RDS_DATABASE
hugging_face_token = HUGGINGFACE_TOKEN

# Function to load the GAIA metadata into MySQL RDS
def load_gaia_metadata_tbl():
    """Loads the GAIA dataset from Hugging Face into an AWS RDS MySQL table"""
    # MySQL connection to AWS RDS
    try:
        connection = get_db_connection()
        if connection.is_connected():
            logging_module.log_success("MySQL connection established successfully.")
    except Error as e:
        logging_module.log_error(f"Error while connecting to MySQL: {e}")
        return

    # Login with Hugging Face token
    try:
        login(token=hugging_face_token)
        logging_module.log_success("Logged in to Hugging Face successfully.")
    except Exception as e:
        logging_module.log_error(f"Failed to login to Hugging Face: {e}")
        return

    # Load the GAIA dataset from Hugging Face
    try:
        ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
        logging_module.log_success("GAIA dataset read from Hugging Face successfully.")
    except Exception as e:
        logging_module.log_error(f"Error reading GAIA dataset from Hugging Face: {e}")
        return

    # Process the dataset and insert into MySQL table
    try:
        validation_df = ds['validation'].to_pandas()
        validation_df['source'] = 'validation'
        test_df = ds['test'].to_pandas()
        test_df['source'] = 'test'

        all_df = pd.concat([validation_df, test_df])
        filtered_df = all_df[all_df['file_name'].str.endswith('.pdf')].copy()
        filtered_df['Annotator Metadata'] = filtered_df['Annotator Metadata'].apply(json.dumps)
        
        cursor = connection.cursor()

        # Drop table if it exists and create a new one
        cursor.execute("DROP TABLE IF EXISTS gaia_metadata_tbl_pdf;")
        logging_module.log_success("Dropped table gaia_metadata_tbl_pdf if it already existed.")

        create_table_query = """
        CREATE TABLE gaia_metadata_tbl_pdf (
            task_id VARCHAR(255),
            Question TEXT,
            Level VARCHAR(3),
            final_answer VARCHAR(255),
            file_name VARCHAR(255),
            file_path VARCHAR(255),
            Annotator_Metadata TEXT,
            source VARCHAR(255),
            s3_url VARCHAR(255),
            file_extension VARCHAR(255),
            unstructured_api_url VARCHAR(255),
            opensource_url VARCHAR(255)
        );
        """
        cursor.execute(create_table_query)
        logging_module.log_success("Table gaia_metadata_tbl_pdf created successfully.")

        # Insert the data into the table
        insert_query = """
        INSERT INTO gaia_metadata_tbl_pdf (task_id, Question, Level, final_answer, file_name, file_path, Annotator_Metadata, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for _, row in filtered_df.iterrows():
            cursor.execute(insert_query, (row['task_id'], row['Question'], row['Level'], row['Final answer'], row['file_name'], row['file_path'], row['Annotator Metadata'], row['source']))

        connection.commit()
        logging_module.log_success("GAIA metadata inserted into AWS RDS successfully.")
    except Exception as e:
        logging_module.log_error(f"Error saving GAIA metadata to MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            logging_module.log_success("MySQL connection closed after metadata insertion.")

# Function to download files from Hugging Face, upload them to S3, and update MySQL RDS
def upload_gaia_files_to_s3_and_update_rds():
    """Downloads GAIA dataset files from Hugging Face, uploads them to AWS S3, and updates the corresponding MySQL RDS records with S3 URLs and file extensions."""
    # MySQL connection to AWS RDS
    try:
        connection = get_db_connection()
        if connection.is_connected():
            logging_module.log_success("MySQL connection established successfully.")
    except Error as e:
        logging_module.log_error(f"Error while connecting to MySQL: {e}")
        return

    # AWS S3 setup
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        logging_module.log_success("Connected to S3 bucket.")
    except Exception as e:
        logging_module.log_error(f"Error connecting to S3: {e}")
        return

    # Hugging Face base URL for validation files
    huggingface_base_url = 'https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/'

    # Fetch records from MySQL and update them with S3 URLs
    try:
        headers = {
            "Authorization": f"Bearer {hugging_face_token}"
        }

        cursor = connection.cursor(dictionary=True)

        # Fetch records where file_name is not null
        select_query = "SELECT * FROM gaia_metadata_tbl_pdf"
        cursor.execute(select_query)
        records = cursor.fetchall()
        logging_module.log_success("Fetched records from gaia_metadata_tbl_pdf.")

        for record in records:
            task_id = record['task_id']
            file_name = record['file_name'].strip()
            category = record['source']

            # Determine the file URL based on the category
            if category == 'validation':
                file_url = huggingface_base_url + 'validation/' + file_name
            else:
                file_url = huggingface_base_url + 'test/' + file_name

            # Download file from Hugging Face and upload it to S3
            try:
                response = requests.get(file_url, headers=headers)
                if response.status_code == 200:
                    file_data = response.content
                    logging_module.log_success(f"Downloaded {file_name} from Hugging Face.")

                    s3_key = f"gaia_files/{file_name}"
                    s3.put_object(Bucket=aws_bucket_name, Key=s3_key, Body=file_data)
                    s3_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{s3_key}"
                    logging_module.log_success(f"Uploaded {file_name} to S3 at {s3_url}")

                    # Update the MySQL table with the S3 URL and file extension
                    try:
                        update_s3url_query = """UPDATE gaia_metadata_tbl_pdf
                                                SET s3_url = %s
                                                WHERE task_id = %s"""
                        cursor.execute(update_s3url_query, (s3_url, task_id))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with S3 URL.")

                        update_file_ext_query = """
                            UPDATE gaia_metadata_tbl_pdf
                            SET file_extension = SUBSTRING_INDEX(file_name, '.', -1)
                            WHERE task_id = %s
                        """
                        cursor.execute(update_file_ext_query, (task_id,))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with file extension.")
                    except Exception as e:
                        logging_module.log_error(f"Error updating S3 URL or file extension for task_id {task_id}: {e}")
                else:
                    logging_module.log_error(f"Failed to download {file_name}: HTTP {response.status_code}")

            except requests.exceptions.RequestException as e:
                logging_module.log_error(f"Error downloading {file_name}: {e}")

    except Error as e:
        logging_module.log_error(f"Error while connecting to MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            logging_module.log_success("MySQL connection closed after file upload to S3.")
