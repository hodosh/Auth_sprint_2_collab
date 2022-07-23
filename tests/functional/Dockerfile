# pull official base image
FROM python:3.10-slim

ENV APP_HOME=/usr/src/app

# set work directory
WORKDIR $APP_HOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "$APP_HOME"

# install psycopg2 dependencies
RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get -y install curl

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

# copy project
COPY .. .
