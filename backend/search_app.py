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

api_dict = load_json("data/api.json")
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

@app.get("/api/stats")
async def get_stats():
    """Get data statistics"""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(api_dict["database_stats_url"])
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                db_data = data.get("data", {})
                return {
                    "total_papers": db_data.get("total_count", 0),
                    "latest_update": db_data.get("latest_update_time", "").split()[0] if db_data.get("latest_update_time") else ""
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Database service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=12312, log_level="info")
