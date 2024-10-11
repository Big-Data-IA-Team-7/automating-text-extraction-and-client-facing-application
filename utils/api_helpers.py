import requests
import pandas as pd
from project_logging import logging_module

def fetch_questions(api_url, headers):
    response = requests.get(f"{api_url}/data/fetch-questions/", headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        logging_module.log_error(f"Error: {response.status_code} - {response.text}")
        return None

def fetch_download_url(api_url, question_selected, dataframe, headers, extraction_method = None):
    df_json = dataframe.to_dict(orient="records")
    payload = {
        "question": question_selected,
        "df": df_json,
        "extraction_method": extraction_method
    }
    response = requests.get(f"{api_url}/data/fetch-download-url/", json=payload, headers=headers)
    return response.json() if response.status_code == 200 else None

def fetch_openai_response(api_url, payload, headers):
    response = requests.get(f"{api_url}/openai/fetch-openai-response/", json=payload, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logging_module.log_error(f"Error: {response.status_code} - {response.text}")
        return None