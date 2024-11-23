#!/bin/bash
source .venv/bin/activate

# Start the FastAPI backend server
uvicorn piframe.app.configurator_backend:app --host 0.0.0.0 --port 8000
