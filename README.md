# A well strucutred FastAPI app with mongodb.

API documentation link - https://localhost:8000/redoc
\
Swagger link -  https://localhost:8000/docs`

## Requirements
- Python (version 3.10+), Docker, Mongodb

## Installation and run locally
### 1. Linux

```bash
# Create python virtual environment
python3 -m venv venv

# Activate the python virtual environment
source venv/bin/activate

# Install the requirements for the project into the virtual environment
pip3 install -r requirements.txt

# Run app locally for local server
fastapi dev

# Run app in production
fastapi run
```

### 2. Windows
Run this project with docker only in windows
```bash
# Build dokcer image
docker build -t backend:latest .

# Run the container to start the app
docker run -p 8000:8000 --rm -d --name backend-app bakcend:latest

```
