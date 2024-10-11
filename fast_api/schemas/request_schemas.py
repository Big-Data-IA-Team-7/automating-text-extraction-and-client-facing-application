from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="The user's unique username")
    password: str = Field(..., min_length=6, description="The user's password, must be at least 6 characters")

class RegisterUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="The user's unique username")
    password: str = Field(..., min_length=6, description="The user's password, must be at least 6 characters")
    first_name: str = Field(None, max_length=50, description="First name of the user (optional)")
    last_name: str = Field(None, max_length=50, description="Last name of the user (optional)")
    email: str = Field(None, max_length=50, description="Email of the user (optional)")

class DownloadRequest(BaseModel):
    question: str
    df: List[Dict]
    extraction_method: Optional[str] = None

class OpenAIRequest(BaseModel):
    model: str = Field(..., min_length=3, max_length=15, description="The model to send the request to")
    question_selected: str = Field(..., description="The question selected by the user")
    file_extract: bool = Field(None, description="Boolean to determine whether file extract API must be used or not (optional)")
    annotated_steps: str = Field(None, description="The annotated steps if any for the question (optional)")
    loaded_file: Dict = Field(None, description="The file to be loaded with OpenAI")