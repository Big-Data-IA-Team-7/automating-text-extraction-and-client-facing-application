from fastapi import APIRouter, HTTPException, status
from fast_api.schemas.request_schemas import LoginRequest, RegisterUserRequest
from fast_api.services.auth_service import hash_password, create_jwt_token
from fast_api.models.user_models import fetch_user_from_db, insert_user

router = APIRouter()

@router.post("/register/")
def register(request: RegisterUserRequest):
    username = request.username
    password = request.password
    first_name = request.first_name
    last_name = request.last_name
    email = request.email
    user = fetch_user_from_db(username)
    if user is None:
        # Insert the user with the hashed password into the database
        insert_user(first_name, username, hash_password(password))  # Ensure this function inserts hashed password
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already exists.',
            headers={"WWW-Authenticate": "Bearer"},
        )
    
@router.post("/login/")
def login(request: LoginRequest):
    username = request.username
    password = request.password
    user = fetch_user_from_db(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found.',
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.iloc[0]["username"] and user.iloc[0]["hashed_password"] == hash_password(password):
        token, expiration = create_jwt_token({"username": username})
        return {"access_token": token,
                "token_type": "bearer",
                "expires": expiration.isoformat(),
                "first_name": user.iloc[0]["first_name"]
                }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password.',
            headers={"WWW-Authenticate": "Bearer"},
        )