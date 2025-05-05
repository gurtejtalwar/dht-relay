from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
app = FastAPI()

# Serve static files (index.html)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace * with frontend IP/domain in production
    allow_methods=["*, GET", "POST, PUT", "DELETE, OPTIONS"],
    allow_headers=["*"],
)

client = motor.motor_asyncio.AsyncIOMotorClient(host=MONGO_HOST, serverSelectionTimeoutMS=5000)
db = client["esp_data"]
data_collection = db["readings"]
settings_collection = db["settings"]

# Data models
class SensorData(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    timestamp: datetime = datetime.utcnow()

class SettingsModel(BaseModel):
    masterSwitch: bool
    tempCutoff: float
    humidityCutoff: float

@app.post("/api/data")
async def receive_data(data: SensorData):
    await data_collection.insert_one(data.dict())
    return {"status": "success"}

@app.get("/api/status")
async def get_status():
    latest = await data_collection.find().sort("timestamp", -1).to_list(1)
    settings = await settings_collection.find_one({"device_id": "esp32-001"})

    if not latest or not settings:
        return {"error": "No data or settings found"}

    doc = latest[0]
    return {
        "temperature": doc["temperature"],
        "humidity": doc["humidity"],
        "masterSwitch": settings["masterSwitch"],
        "tempCutoff": settings["tempCutoff"],
        "humidityCutoff": settings["humidityCutoff"]
    }

@app.post("/api/settings")
async def update_settings(settings: SettingsModel):
    await settings_collection.update_one(
        {"device_id": "esp32-001"},
        {"$set": settings.dict()},
        upsert=True
    )
    return {"status": "success"}