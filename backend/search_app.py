#!/usr/bin/env python3
"""
Simple HTTP server for serving JSON data
"""
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils import *

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/config")
async def get_config():
    """Get configuration data"""
    return load_json("data/config.json")

@app.get("/api/test_data")
async def get_test_data():
    """Get test data"""
    return load_json("data/test_data.json") * 5

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=12312, log_level="info")
