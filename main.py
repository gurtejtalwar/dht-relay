from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_HOST = os.getenv("MONGO_HOST")
app = FastAPI()

client = motor.motor_asyncio.AsyncIOMotorClient(host=MONGO_HOST, serverSelectionTimeoutMS=5000)
db = client["ritz"]
dht_collection = db["dht11"]
relay_collection = db["relay"]
settings_collection = db["settings"]

class DHT11(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    timestamp: datetime = datetime.utcnow()

@app.post("/api/data")
async def receive_data(data: DHT11):
    await dht_collection.insert_one(data.dict())
    return {"status": "success"}
