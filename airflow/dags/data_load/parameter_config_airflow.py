import boto3
from botocore.exceptions import ClientError

# Define the parameter names to be retrieved
parameter_names = [
    'ACCESS_KEY_ID_AWS',
    'SECRET_ACCESS_KEY_AWS',
    'RDS_HOST_AWS',
    'RDS_USERNAME_AWS',
    'RDS_PASSWORD_AWS',
    'RDS_DB_PORT_AWS',
    'RDS_DATABASE_AWS',
    'SECRET_KEY',
    'HUGGINGFACE_TOKEN',
    'S3_BUCKET_NAME_AWS',
    'UNSTRUCTURED_API_KEY',
    'UNSTRUCTURED_API_URL',
    'S3_URL_AWS',
    'S3_OUTPUT_URI_AWS'
]

# Create an SSM client
ssm_client = boto3.client('ssm', region_name='us-east-1')  # Replace 'us-east-1' with your AWS region

# Split the parameters into batches
batch_1 = ['ACCESS_KEY_ID_AWS', 'SECRET_ACCESS_KEY_AWS', 'RDS_HOST_AWS', 'RDS_USERNAME_AWS', 'RDS_PASSWORD_AWS', 'RDS_DB_PORT_AWS', 'RDS_DATABASE_AWS', 'SECRET_KEY', 'HUGGINGFACE_TOKEN', 'S3_BUCKET_NAME_AWS']
batch_2 = ['UNSTRUCTURED_API_KEY', 'UNSTRUCTURED_API_URL', 'S3_URL_AWS', 'S3_OUTPUT_URI_AWS']

# Fetch first batch of parameters
response_1 = ssm_client.get_parameters(Names=batch_1, WithDecryption=True)
parameters_1 = {param['Name']: param['Value'] for param in response_1['Parameters']}

# Fetch second batch of parameters
response_2 = ssm_client.get_parameters(Names=batch_2, WithDecryption=True)
parameters_2 = {param['Name']: param['Value'] for param in response_2['Parameters']}

# Store the values in variables
AWS_ACCESS_KEY_ID = parameters_1.get('ACCESS_KEY_ID_AWS')
AWS_SECRET_ACCESS_KEY = parameters_1.get('SECRET_ACCESS_KEY_AWS')
AWS_RDS_HOST = parameters_1.get('RDS_HOST_AWS')
AWS_RDS_USERNAME = parameters_1.get('RDS_USERNAME_AWS')
AWS_RDS_PASSWORD = parameters_1.get('RDS_PASSWORD_AWS')
AWS_RDS_DB_PORT = parameters_1.get('RDS_DB_PORT_AWS')
AWS_RDS_DATABASE = parameters_1.get('RDS_DATABASE_AWS')
UNSTRUCTURED_API_KEY = parameters_2.get('UNSTRUCTURED_API_KEY')
UNSTRUCTURED_API_URL = parameters_2.get('UNSTRUCTURED_API_URL')
SECRET_KEY = parameters_1.get('SECRET_KEY')
AWS_S3_URL = parameters_2.get('S3_URL_AWS')
AWS_S3_OUTPUT_URI = parameters_2.get('S3_OUTPUT_URI_AWS')
AWS_S3_BUCKET_NAME = parameters_1.get('S3_BUCKET_NAME_AWS')
HUGGINGFACE_TOKEN = parameters_1.get('HUGGINGFACE_TOKEN')

# Save specific variables to .env file
with open('/tmp/env_file.sh', 'w') as env_file:  # You can choose any file path
    env_file.write(f'export AWS_ACCESS_KEY_ID="{AWS_ACCESS_KEY_ID}"\n')
    env_file.write(f'export AWS_SECRET_ACCESS_KEY="{AWS_SECRET_ACCESS_KEY}"\n')
    env_file.write(f'export UNSTRUCTURED_API_KEY="{UNSTRUCTURED_API_KEY}"\n')
    env_file.write(f'export UNSTRUCTURED_API_URL="{UNSTRUCTURED_API_URL}"\n')
    env_file.write(f'export AWS_S3_OUTPUT_URI="{AWS_S3_OUTPUT_URI}"\n')
    env_file.write(f'export AWS_S3_URL="{AWS_S3_URL}"\n')
