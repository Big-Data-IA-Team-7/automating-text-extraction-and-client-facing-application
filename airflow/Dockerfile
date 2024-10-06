# Use the official Airflow image as the base
FROM apache/airflow:2.10.2

# Set environment variables (optional)
ENV AIRFLOW_HOME=/opt/airflow

# Copy your requirements.txt file to the Docker image
COPY requirements.txt .

# Install Python packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Airflow Webserver port
EXPOSE 8080

# Initialize Airflow database
RUN airflow db init

# Set the default entrypoint for Airflow (webserver, scheduler, etc.)
CMD ["airflow", "webserver"]
