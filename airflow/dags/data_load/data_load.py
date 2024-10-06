import os
from datasets import load_dataset
from huggingface_hub import login
import json
import boto3
import requests
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import data_load.data_storage_log as logging_module
import pandas as pd
import logging

# Load environment variables
load_dotenv()

def load_gaia_metadata_tbl():
    # Getting environmental variables
    hugging_face_token = os.getenv('HUGGINGFACE_TOKEN')
    aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    aws_rds_host = os.getenv('AWS_RDS_HOST')
    aws_rds_user = os.getenv('AWS_RDS_USERNAME')
    aws_rds_password = os.getenv('AWS_RDS_PASSWORD')
    aws_rds_port = os.getenv('AWS_RDS_DB_PORT')
    aws_rds_database = os.getenv('AWS_RDS_DATABASE')

    # MySQL connection to AWS RDS using MySQL Connector
    try:
        connection = mysql.connector.connect(
            host=aws_rds_host,
            user=aws_rds_user,
            password=aws_rds_password,
            database=aws_rds_database,
            port=aws_rds_port
        )
        if connection.is_connected():
            logging_module.log_success("MySQL connection established successfully.")
    except Error as e:
        logging_module.log_error(f"Error while connecting to MySQL: {e}")
        return

    # Login with the Hugging Face token
    try:
        login(token=hugging_face_token)
        logging_module.log_success("Logged in to Hugging Face successfully.")
    except Exception as e:
        logging_module.log_error(f"Failed to login to Hugging Face: {e}")
        return

    # Load the GAIA dataset
    try:
        ds = load_dataset("gaia-benchmark/GAIA", "2023_all")
        logging_module.log_success("GAIA dataset loaded successfully.")
    except Exception as e:
        logging_module.log_error(f"Error loading GAIA dataset: {e}")
        return

    # Convert the 'validation' split into a pandas DataFrame
    try:
        validation_df = ds['validation'].to_pandas()
        validation_df['source'] = 'validation'
        test_df = ds['test'].to_pandas()
        test_df['source'] = 'test'

        all_df = pd.concat([validation_df, test_df])
        filtered_df = all_df[all_df['file_name'].str.endswith('.pdf')].copy()
        filtered_df['Annotator Metadata'] = filtered_df['Annotator Metadata'].apply(json.dumps)
        
        # Insert DataFrame into MySQL database using MySQL Connector
        cursor = connection.cursor()
        
        # Drop table if it already exists
        drop_table_query = "DROP TABLE IF EXISTS gaia_metadata_tbl_pdf;"
        cursor.execute(drop_table_query)
        logging_module.log_success("Dropped table gaia_metadata_tbl_pdf if it already existed.")
        
        # Create the table
        create_table_query = """
        CREATE TABLE gaia_metadata_tbl_pdf (
            task_id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255),
            Annotator_Metadata TEXT,
            source VARCHAR(255),
            s3_url VARCHAR(255),
            file_extension VARCHAR(255)
        );
        """
        cursor.execute(create_table_query)
        logging_module.log_success("Table gaia_metadata_tbl_pdf created successfully.")
        
        # Insert rows from DataFrame into the MySQL table
        insert_query = """
        INSERT INTO gaia_metadata_tbl_pdf (file_name, Annotator_Metadata, source)
        VALUES (%s, %s, %s)
        """
        for _, row in filtered_df.iterrows():
            cursor.execute(insert_query, (row['file_name'], row['Annotator Metadata'], row['source']))
        connection.commit()
        logging_module.log_success("GAIA dataset inserted into AWS RDS - bdia_team7_db successfully.")
    except Exception as e:
        logging_module.log_error(f"Error saving GAIA dataset to MySQL: {e}")
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

    # Connect to MySQL RDS and fetch records where file_name is not null
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

            # Download file from Hugging Face
            if category == 'validation':
                file_url = huggingface_base_url + 'validation/' + file_name
            else:
                file_url = huggingface_base_url + 'test/' + file_name
            try:
                response = requests.get(file_url, headers=headers)
                if response.status_code == 200:
                    file_data = response.content
                    logging_module.log_success(f"Downloaded {file_name} from Hugging Face.")

                    # Upload the file to S3
                    s3_key = f"gaia_files/{file_name}"
                    s3.put_object(Bucket=aws_bucket_name, Key=s3_key, Body=file_data)
                    s3_url = f"https://{aws_bucket_name}.s3.amazonaws.com/{s3_key}"
                    logging_module.log_success(f"Uploaded {file_name} to S3 at {s3_url}")

                    # Update the original RDS record with the S3 URL
                    try:
                        update_s3url_query = """UPDATE gaia_metadata_tbl_pdf
                                                SET s3_url = %s
                                                WHERE task_id = %s"""
                        cursor.execute(update_s3url_query, (s3_url, task_id))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with S3 URL.")
                    except Exception as e:
                        logging_module.log_error(f"Error updating S3 URL for task_id {task_id}: {e}")

                    # Update the original RDS record with the file extension
                    try:
                        update_file_ext_query = """
                            UPDATE gaia_metadata_tbl_pdf
                            SET file_extension = SUBSTRING_INDEX(file_name, '.', -1)
                            WHERE task_id = %s
                        """
                        cursor.execute(update_file_ext_query, (task_id,))
                        connection.commit()
                        logging_module.log_success(f"Updated record {task_id} with file extension.")
                    except Exception as e:
                        logging_module.log_error(f"Error updating file extension for task_id {task_id}: {e}")

                else:
                    logging_module.log_error(f"Failed to download {file_name}: HTTP {response.status_code}")

            except requests.exceptions.RequestException as e:
                logging_module.log_error(f"Error downloading {file_name}: {e}")

    except Error as e:
        logging_module.log_error(f"Error while connecting to MySQL: {e}")

    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
                logging_module.log_success("MySQL connection is closed.")
        except Exception as e:
            logging_module.log_error(f"Error closing MySQL connection: {e}")

#load_gaia_metadata_tbl()
