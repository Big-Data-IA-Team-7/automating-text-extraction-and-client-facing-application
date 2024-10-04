from airflow.models.dag import DAG
from airflow.decorators import task
from datetime import datetime, timedelta

import os
import dotenv

from unstructured_ingest.v2.pipeline.pipeline import Pipeline
from unstructured_ingest.v2.interfaces import ProcessorConfig
from unstructured_ingest.v2.processes.connectors.fsspec.s3 import (
    S3IndexerConfig,
    S3DownloaderConfig,
    S3ConnectionConfig,
    S3AccessConfig,
    S3UploaderConfig
)
from unstructured_ingest.v2.processes.partitioner import PartitionerConfig

@task
def extract_pdf_unstructured():

    # Get the parent directory path (where your .env file is located)
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Construct the full path to the .env file
    env_path = os.path.join(parent_dir, '.env')
    dotenv.load_dotenv(env_path)
    Pipeline.from_configs(
        context=ProcessorConfig(),
        indexer_config=S3IndexerConfig(remote_url=os.getenv("AWS_S3_URL")),
        downloader_config=S3DownloaderConfig(),
        source_connection_config=S3ConnectionConfig(
            access_config=S3AccessConfig(
                key=os.getenv("AWS_ACCESS_KEY_ID"),
                secret=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        ),
        partitioner_config=PartitionerConfig(
            partition_by_api=True,
            api_key=os.getenv("UNSTRUCTURED_API_KEY"),
            partition_endpoint=os.getenv("UNSTRUCTURED_API_URL"),
            strategy="fast",
            additional_partition_args={
                "split_pdf_page": True,
                "split_pdf_allow_failed": True,
                "split_pdf_concurrency_level": 15
            }
        ),
        destination_connection_config=S3ConnectionConfig(
            access_config=S3AccessConfig(
                key=os.getenv("AWS_ACCESS_KEY_ID"),
                secret=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
        ),
        uploader_config=S3UploaderConfig(remote_url=os.getenv("AWS_S3_OUTPUT_URI"))        
    ).run()

with DAG(
    "tutorial",
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args={
        "depends_on_past": False,
        "email": ["bigdatafall24team7@gmail.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        # 'queue': 'bash_queue',
        # 'pool': 'backfill',
        # 'priority_weight': 10,
        # 'end_date': datetime(2016, 1, 1),
        # 'wait_for_downstream': False,
        # 'sla': timedelta(hours=2),
        # 'execution_timeout': timedelta(seconds=300),
        # 'on_failure_callback': some_function, # or list of functions
        # 'on_success_callback': some_other_function, # or list of functions
        # 'on_retry_callback': another_function, # or list of functions
        # 'sla_miss_callback': yet_another_function, # or list of functions
        # 'on_skipped_callback': another_function, #or list of functions
        # 'trigger_rule': 'all_success'
    },
    description="A simple tutorial DAG",
    schedule=timedelta(days=1),
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example"],
) as dag:

    # t1, t2 and t3 are examples of tasks created by instantiating operators
    extract_pdf_unstructured()