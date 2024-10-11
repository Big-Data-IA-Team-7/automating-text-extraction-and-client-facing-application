#!/bin/bash

# Echo to show the process has started
echo 'Starting the Bash script and importing variables from Python'

# Import variables from Python using absolute path
eval $(python3 /opt/airflow/dags/data_load/parameter_config_airflow.py)


# Now, run your Python pipeline script
python /opt/airflow/dags/data_load/pdf_extraction_unstructured.py

# Echo to indicate the process has completed
echo 'Python script executed successfully'
