FROM python:3.12.6

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./fast_api /code/fast_api
COPY ./streamlit_app.py /code/streamlit_app.py

CMD ["/bin/bash", "-c", "uvicorn fast_api.fast_api_setup:app --host 0.0.0.0 --port 8000 --reload & streamlit run streamlit_app.py --server.port 8501"]