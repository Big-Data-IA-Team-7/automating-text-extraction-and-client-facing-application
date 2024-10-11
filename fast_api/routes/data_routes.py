from fastapi import APIRouter, HTTPException, status, Depends
from fast_api.schemas.request_schemas import DownloadRequest
from fast_api.services.auth_service import get_current_user
from fast_api.services.data_service import fetch_data_from_db, download_file
import pandas as pd
from typing import List, Dict
from project_logging import logging_module

router = APIRouter()

@router.get("/fetch-questions/", response_model=List[dict])
def get_questions_for_user(current_user: Dict = Depends(get_current_user)):

    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is fetching data from the database.")

    # Fetch data from the database
    data = fetch_data_from_db()

    if isinstance(data, pd.DataFrame):
        return data.to_dict(orient="records")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No data returned from the database",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/fetch-download-url/", response_model=Dict)
def get_download_url(request: DownloadRequest, current_user: Dict = Depends(get_current_user)):

    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is fetching data from the database.")

        # Convert the request df back to a DataFrame
    df = pd.DataFrame(request.df)
    question = request.question
    extraction_method = request.extraction_method

    logging_module.log_success(f"Question: {question}, Extraction Method: {extraction_method}")

    download_url = download_file(question, df, extraction_method)
                  
    return download_url