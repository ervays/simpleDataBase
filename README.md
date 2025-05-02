# Simple Hello World API

A basic Hello World API server that runs on port 8080.

## Features

- Express.js REST API
- Returns a simple JSON response
- Containerized with Docker

## Getting Started

### Prerequisites

- Node.js (for local development)
- Docker (for containerized deployment)

### Local Development

1. Install dependencies:
   ```
   npm install
   ```

2. Start the server:
   ```
   npm start
   ```

3. Access the API at http://localhost:8080

### Docker Deployment

1. Build the Docker image:
   ```
   docker build -t hello-world-api .
   ```

2. Run the container:
   ```
   docker run -p 8080:8080 hello-world-api
   ```

3. Access the API at http://localhost:8080

## API Endpoints

- `GET /`: Returns a JSON response with "Hello World!" message