FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir flask flask-cors

EXPOSE 5000

# Run database schema update on startup
CMD python db_update.py && python api_server.py