FROM python:3.9-slim-buster
ARG SERVER_NAME
ENV SERVER_NAME=${SERVER_NAME}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8000
# Use Uvicorn to run the FastAPI application
# --host 0.0.0.0: Binds to all network interfaces
# --port 8000: Listens on port 8000
# app:app: Refers to the 'app' object in app.py
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]