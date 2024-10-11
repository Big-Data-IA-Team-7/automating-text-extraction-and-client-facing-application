from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from data_load.data_load import load_gaia_metadata_tbl
from data_load.data_load import upload_gaia_files_to_s3_and_update_rds 
from data_load.pdf_extraction_open_source import process_pdf_open_source
from airflow.operators.bash import BashOperator
from data_load.update_url_froms3 import update_metadata_with_s3_urls

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 4),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
    'execute_tasks_new_python_interpreter': True
}

# Define the DAG
dag = DAG(
    'trigger_pdf_extract_load',
    default_args=default_args,
    description='DAG to trigger and extract information from the GAIA dataset PDFs',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Define PythonOperator tasks
load_gaia_metadata_tbl = PythonOperator(
    task_id='load_gaia_metadata_tbl',
    python_callable=load_gaia_metadata_tbl,
    dag=dag
)

# Task to load PDF files into S3 and update metadata in RDS
load_pdf_files_into_s3 = PythonOperator(
    task_id='load_pdf_files_into_s3',
    python_callable=upload_gaia_files_to_s3_and_update_rds,
    dag=dag
)

# Task to process PDFs using an open-source tool
process_pdfs_open_source_task = PythonOperator(
        task_id='process_pdfs_open_source_task',
        python_callable=process_pdf_open_source,  # Reference the function
        dag=dag
)

'''process_pdfs_using_unstructured = PythonOperator(
        task_id='process_pdfs_using_unstructured',
        python_callable=run_unstructured_pipeline,  # Reference the function
        dag=dag
)'''

# Task to run a bash script for unstructured PDF processing
process_pdfs_using_unstructured = BashOperator(
    task_id='run_unstructured_using_bash',
    bash_command='data_load/run_unstructured.sh',  # Path to the bash script
    dag=dag
)

# Task to update metadata with S3 URLs for open source processed PDFs
update_s3url_open_source = PythonOperator(
    task_id='update_s3url_open_source',
    python_callable=update_metadata_with_s3_urls,
    op_args=['open_source_processed/'],
    dag=dag
)

# Task to update metadata with S3 URLs for unstructured processed PDFs
update_s3url_unstructured = PythonOperator(
    task_id='update_s3url_unstructured',
    python_callable=update_metadata_with_s3_urls,
    op_args=['unstructured_extract/'],
    dag=dag
)

# Define task dependencies
load_gaia_metadata_tbl >> load_pdf_files_into_s3
load_pdf_files_into_s3 >> process_pdfs_open_source_task >> update_s3url_open_source
load_pdf_files_into_s3 >> process_pdfs_using_unstructured >> update_s3url_unstructured

# Function Comments:
# load_gaia_metadata_tbl: This function is responsible for loading the GAIA metadata into a target table. It sets up the initial metadata required for downstream PDF processing.
# upload_gaia_files_to_s3_and_update_rds: This function uploads GAIA PDF files into an S3 bucket and updates the RDS database with the respective metadata.
# process_pdf_open_source: This function extracts data from GAIA PDFs using open-source tools. It processes the PDFs to retrieve valuable information and store it in a structured format.
# update_metadata_with_s3_urls: This function updates the metadata table with URLs pointing to the processed PDF files in S3, enabling easy access to extracted data.
# run_unstructured_using_bash: This bash script task allows for processing PDFs using an unstructured extraction method, giving flexibility to use custom scripts or tools for more complex use cases.

# DAG Comments:
# - The DAG is responsible for processing PDFs from the GAIA dataset.
# - The workflow consists of loading metadata, uploading files to S3, extracting data using two different methods (open-source and unstructured extraction), and updating metadata with S3 URLs.
# - Dependencies between tasks are defined to ensure that the operations are performed in the correct sequence.