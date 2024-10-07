from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from data_load.data_load import load_gaia_metadata_tbl
from data_load.data_load import upload_gaia_files_to_s3_and_update_rds 
from data_load.pdf_extraction_open_source import process_pdf_open_source
from airflow.operators.bash import BashOperator
#from data_load.unstructured_file_extract import run_unstructured_pipeline
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



load_pdf_files_into_s3 = PythonOperator(
    task_id='load_pdf_files_into_s3',
    python_callable=upload_gaia_files_to_s3_and_update_rds,
    dag=dag
)

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

process_pdfs_using_unstructured = BashOperator(
    task_id='run_unstructured_using_bash',
    bash_command='data_load/run_unstructured.sh',  # Path to the bash script
    dag=dag
)

update_s3url_open_source = PythonOperator(
    task_id='update_s3url_open_source',
    python_callable=update_metadata_with_s3_urls,
    op_args=['open_source_processed/'],
    dag=dag
)

update_s3url_unstructured = PythonOperator(
    task_id='update_s3url_unstructured',
    python_callable=update_metadata_with_s3_urls,
    op_args=['unstructured_extract/'],
    dag=dag
)

load_gaia_metadata_tbl >> load_pdf_files_into_s3
load_pdf_files_into_s3 >> process_pdfs_open_source_task >> update_s3url_open_source
load_pdf_files_into_s3 >> process_pdfs_using_unstructured >> update_s3url_unstructured