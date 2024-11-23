from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from typing import Dict, Any
import boto3
from pydantic import BaseModel

from piframe.config import Config
from piframe.hardware import power
from piframe import prompts

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Remove credentials requirement
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = "config.json"

# Pydantic models for request/response
class PowerStatus(BaseModel):
    is_battery_powered: bool
    battery_level: float | None
    power_status_string: str

class ConfigUpdate(BaseModel):
    config: Dict[str, Any]

@app.get("/api/models")
async def get_models():
    """Get available Bedrock models"""
    bedrock = boto3.client("bedrock")
    models = bedrock.list_foundation_models()["modelSummaries"]
    return {"models": models}

@app.get("/api/power")
async def get_power():
    """Get current power status"""
    battery_level = power.get_battery_level()
    is_battery = power.is_battery_powered()

    return PowerStatus(
        is_battery_powered=is_battery,
        battery_level=battery_level,
        power_status_string="Battery" if is_battery else "Plugged in"
    )

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Config file not found")

@app.post("/api/config")
async def save_config(config_update: ConfigUpdate):
    """Save configuration"""
    try:
        config = Config(**config_update.config)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        return {"message": "Configuration saved!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/refresh")
async def refresh_image():
    """Trigger screen refresh"""
    try:
        os.system("sudo systemctl start update-frame")
        return {"message": "Screen will refresh soon!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
