from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from data_load.data_load import load_gaia_metadata_tbl 
from data_load.pdf_extraction_open_source import process_all_pdfs_in_s3_directory
from airflow.operators.bash import BashOperator
from data_load.unstructured_file_extract import run_unstructured_pipeline




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

process_pdfs_task = PythonOperator(
        task_id='process_all_pdfs_in_s3_directory',
        python_callable=process_all_pdfs_in_s3_directory,  # Reference the function
        op_args=['gaia-dataset-assignment-2', 'gaia-dataset-assignment-2', 'Processing_files24'],  # Pass arguments here
        dag=dag
)

'''process_pdfs_using_unstructured = PythonOperator(
        task_id='process_pdfs_using_unstructured',
        python_callable=run_unstructured_pipeline,  # Reference the function
        dag=dag
)'''

process_pdfs_using_unstructured = BashOperator(
    task_id='run_unstructured_using_bash',
    bash_command='data_load/run_unstructured.sh',  # Path to the bash script
    dag=dag
)


load_gaia_metadata_tbl >> process_pdfs_task
load_gaia_metadata_tbl >> process_pdfs_using_unstructured