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

# Set the start method for multiprocessing to avoid the "bootstrap" error
set_start_method("spawn", force=True)  # "spawn" is safer on most systems

def run_unstructured_pipeline():
    try:
        logging.info("Starting the Unstructured Pipeline")
        print("Starting the Unstructured Pipeline")

        # Fetch the environment variables
        aws_s3_url = os.getenv("AWS_S3_URL")
        aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        unstructured_api_key = os.getenv("UNSTRUCTURED_API_KEY")
        unstructured_api_url = os.getenv("UNSTRUCTURED_API_URL")
        aws_s3_output_uri = os.getenv("AWS_S3_OUTPUT_URI")

        # Check if any of the required environment variables are missing
        if not all([aws_s3_url, aws_access_key, aws_secret_key, unstructured_api_key, unstructured_api_url, aws_s3_output_uri]):
            logging.error("One or more environment variables are missing")
            raise ValueError("Required environment variables are missing. Please check your .env file.")

        # Run the pipeline
        Pipeline.from_configs(
            context=ProcessorConfig(),
            indexer_config=S3IndexerConfig(remote_url=aws_s3_url),
            downloader_config=S3DownloaderConfig(),
            source_connection_config=S3ConnectionConfig(
                access_config=S3AccessConfig(
                    key=aws_access_key,
                    secret=aws_secret_key
                )
            ),
            partitioner_config=PartitionerConfig(
                partition_by_api=True,
                api_key=unstructured_api_key,
                partition_endpoint=unstructured_api_url,
                strategy="hi_res",
                additional_partition_args={
                    "split_pdf_page": True,
                    "split_pdf_allow_failed": True,
                    "split_pdf_concurrency_level": 15,
                    "infer_table_structure": True,
                    "extract_images_in_pdf": True,
                    "extract_image_block_types": ["Image"]
                }
            ),
            destination_connection_config=S3ConnectionConfig(
                access_config=S3AccessConfig(
                    key=aws_access_key,
                    secret=aws_secret_key
                )
            ),
            uploader_config=S3UploaderConfig(remote_url=aws_s3_output_uri)
        ).run()
        logging.info("Pipeline executed successfully")
        print("Pipeline executed successfully")
    except Exception as e:
        logging.error(f"Error occurred in unstructured pipeline: {e}")
        print(f"Error occurred in unstructured pipeline: {e}")
        with open("pipeline_error.log", "a") as f:
            f.write(f"Error: {e}\\n")


if __name__ == "__main__":
    run_unstructured_pipeline()