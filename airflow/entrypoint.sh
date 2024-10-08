#!/bin/bash

# Set your secret name or ARN here
SECRET_ID="arn:aws:secretsmanager:us-east-1:054037097981:secret:airflow-secrets-FWgOWu"

# Set your AWS region
AWS_REGION="us-east-1"

# Retrieve the secret value
SECRET_VALUE=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --region "$AWS_REGION" --query SecretString --output text)

# Check if the secret was retrieved successfully
if [ $? -ne 0 ]; then
    echo "Failed to retrieve the secret. Please check your AWS credentials and permissions."
    exit 1
fi

# Parse the JSON and create .env file
echo "$SECRET_VALUE" | jq -r 'to_entries|map("\(.key)=\(.value)")|.[]' > $AIRFLOW_HOME/.env

# Check if .env file was created successfully
if [ $? -ne 0 ]; then
    echo "Failed to create .env file. Please check if the secret value is a valid JSON."
    exit 1
fi

echo "Secret retrieved and .env file created successfully."

# Source the .env file to set environment variables
set -a
source $AIRFLOW_HOME/.env
set +a

# Execute the provided command (CMD from Dockerfile)
exec "$@"