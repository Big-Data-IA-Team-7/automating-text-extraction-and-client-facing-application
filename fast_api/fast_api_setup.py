from .routes import auth_routes, data_routes, openai_routes
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

# Create FastAPI instance
app = FastAPI()

# Include the routers
app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(data_routes.router, prefix="/data", tags=["data"])
app.include_router(openai_routes.router, prefix="/openai", tags=["openai"])
