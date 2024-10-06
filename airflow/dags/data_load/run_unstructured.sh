#!/bin/bash

# Echo to show the process has started
echo "Starting the Bash script and running Python pipeline script"

# Run the Python code inline using python -c
python -c "
from multiprocessing import set_start_method, Process
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
import logging

# Set the start method for multiprocessing to avoid the 'bootstrap' error
set_start_method('spawn', force=True)  # 'spawn' is safer on most systems

def run_unstructured_pipeline():
    try:
        logging.info('Starting the Unstructured Pipeline')
        print('Starting the Unstructured Pipeline')
        dotenv.load_dotenv('.env')

        # Run the pipeline
        Pipeline.from_configs(
            context=ProcessorConfig(),
            indexer_config=S3IndexerConfig(remote_url=os.getenv('AWS_S3_URL')),
            downloader_config=S3DownloaderConfig(),
            source_connection_config=S3ConnectionConfig(
                access_config=S3AccessConfig(
                    key=os.getenv('AWS_ACCESS_KEY_ID'),
                    secret=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
            ),
            partitioner_config=PartitionerConfig(
                partition_by_api=True,
                api_key=os.getenv('UNSTRUCTURED_API_KEY'),
                partition_endpoint=os.getenv('UNSTRUCTURED_API_URL'),
                strategy='hi_res',
                additional_partition_args={
                    'split_pdf_page': True,
                    'split_pdf_allow_failed': True,
                    'split_pdf_concurrency_level': 15,
                    'infer_table_structure': True,
                    'extract_images_in_pdf': True,
                    'extract_image_block_types': ['Image']
                }
            ),
            destination_connection_config=S3ConnectionConfig(
                access_config=S3AccessConfig(
                    key=os.getenv('AWS_ACCESS_KEY_ID'),
                    secret=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
            ),
            uploader_config=S3UploaderConfig(remote_url=os.getenv('AWS_S3_OUTPUT_URI'))
        ).run()
        logging.info('Pipeline executed successfully')
        print('Pipeline executed successfully')
    except Exception as e:
        logging.error(f'Error occurred in unstructured pipeline: {e}')
        print(f'Error occurred in unstructured pipeline: {e}')
        with open('pipeline_error.log', 'a') as f:
            f.write(f'Error: {e}\\n')


if __name__ == '__main__':
    run_unstructured_pipeline()
"

# Echo to indicate the process has completed
echo "Python script executed successfully"
