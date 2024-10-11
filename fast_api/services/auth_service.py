import os, base64, hmac, hashlib, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from fast_api.models.user_models import fetch_user_from_db
from project_logging import logging_module
from parameter_config import SECRET_KEY

security = HTTPBearer()

def hash_password(password: str) -> str:
    secret_key = base64.b64decode(SECRET_KEY)
    hash_object = hmac.new(secret_key, msg=password.encode(), digestmod=hashlib.sha256)
    hash_hex = hash_object.hexdigest()
    return hash_hex

def create_jwt_token(data: dict):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=50)
    token_payload = {"exp": expiration, **data}
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')
    return token, expiration

def decode_jwt_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expired',
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid token',
            headers={"WWW-Authenticate": "Bearer"},
        )
    
def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    token = authorization.credentials
    try:
        payload = decode_jwt_token(token)
        username = payload.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token payload',
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = fetch_user_from_db(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found',
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.to_dict(orient="records")[0]
    except HTTPException as e:
        logging_module.log_error(f"An unexpected error occurred: {e}")
        return e