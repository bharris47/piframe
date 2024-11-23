#!/bin/bash
source .venv/bin/activate

# Start the FastAPI backend server
uvicorn piframe.app.configurator_backend:app --port 8000
