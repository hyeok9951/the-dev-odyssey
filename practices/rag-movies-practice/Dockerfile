FROM python:3.11

WORKDIR /app

COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./backend/ /app/