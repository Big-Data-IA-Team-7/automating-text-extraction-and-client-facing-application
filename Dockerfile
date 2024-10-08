# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file (relative path)
COPY requirements.txt /app/requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the FastAPI folder (including both FastApi.py and database.py)
COPY fast_api/ /app/fast_api/

# Copy the Streamlit application file
COPY streamlit_app.py /app/streamlit_app.py

# Copy other necessary files and directories
COPY auth/ /app/auth/
COPY data/ /app/data/
COPY fast_api/ /app/fast_api
COPY features/  /app/features
COPY project_logging/ /app/project_logging/
COPY utils/ /app/utils
# Copy the .env file
COPY .env /app/.env


# Expose the ports for FastAPI and Streamlit
EXPOSE 8000 8501

# Start both FastAPI and Streamlit
CMD ["sh", "-c", "uvicorn FastAPI.FastApi:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port=8501 --server.enableCORS=false"]
