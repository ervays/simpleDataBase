FROM python:3.9-slim

# Install required dependencies
RUN apt-get update && apt-get install -y sqlite3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY schema.sql /app/
COPY example.py /app/
COPY requirements.txt /app/
COPY create_admin.py /app/
COPY api_server.py /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create and initialize the database with schema
RUN sqlite3 auth.db < schema.sql

# Initialize admin user
RUN python create_admin.py

# Expose port for the API
EXPOSE 5000

# Start the API server when the container launches
CMD ["python", "api_server.py"]