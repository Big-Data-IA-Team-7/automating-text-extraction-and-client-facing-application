import boto3

# Define the parameter names to be retrieved
parameter_names = [
    'ACCESS_KEY_ID_AWS',
    'SECRET_ACCESS_KEY_AWS',
    'RDS_HOST_AWS',
    'RDS_USERNAME_AWS',
    'RDS_PASSWORD_AWS',
    'RDS_DB_PORT_AWS',
    'RDS_DATABASE_AWS',
    'OPENAI_API_KEY',
    'SECRET_KEY',
    'FASTAPI_DEV_URL'
]

# Create an SSM client
ssm_client = boto3.client('ssm', region_name='us-east-1')  # Replace 'your-region' with your AWS region

# Retrieve parameters from AWS SSM Parameter Store
response = ssm_client.get_parameters(
    Names=parameter_names,
    WithDecryption=True  # Ensure secure strings are decrypted
)

# Extract parameters from the response
parameters = response.get('Parameters', [])
parameters_dict = {param['Name']: param['Value'] for param in parameters}

# Store the values in variables
ACCESS_KEY_ID_AWS = parameters_dict.get('ACCESS_KEY_ID_AWS')
SECRET_ACCESS_KEY_AWS = parameters_dict.get('SECRET_ACCESS_KEY_AWS')
RDS_HOST_AWS = parameters_dict.get('RDS_HOST_AWS')
RDS_USERNAME_AWS = parameters_dict.get('RDS_USERNAME_AWS')
RDS_PASSWORD_AWS = parameters_dict.get('RDS_PASSWORD_AWS')
RDS_DB_PORT_AWS = parameters_dict.get('RDS_DB_PORT_AWS')
RDS_DATABASE_AWS = parameters_dict.get('RDS_DATABASE_AWS')
OPENAI_API_KEY = parameters_dict.get('OPENAI_API_KEY')
SECRET_KEY = parameters_dict.get('SECRET_KEY')
FAST_API_DEV_URL = parameters_dict.get('FASTAPI_DEV_URL')