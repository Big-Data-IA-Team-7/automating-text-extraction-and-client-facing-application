from fastapi import APIRouter, Depends
from fast_api.schemas.request_schemas import OpenAIRequest
from fast_api.services.auth_service import get_current_user
from fast_api.services.openai_service import OpenAIClient
from project_logging import logging_module
from typing import Dict, Optional

router = APIRouter()

@router.get("/fetch-openai-response/", response_model=Optional[str])
def get_openai_response(request: OpenAIRequest, current_user: Dict = Depends(get_current_user)):
    
    # Log the user who is making the request
    logging_module.log_success(f"User '{current_user['username']}' is sending request to OpenAI.")

    question_selected = request.question_selected
    model = request.model
    annotated_steps = request.annotated_steps
    file_extract = request.file_extract
    loaded_file = request.loaded_file
    
    client = OpenAIClient()

    if file_extract and loaded_file:
        response = client.file_validation_prompt(loaded_file["path"], question_selected, model)
    else:
        response = client.validation_prompt(question_selected, model, annotated_steps)

    return response