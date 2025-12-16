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

@app.get("/api/search")
async def search(query: str = "Agentic Reinforcement Learning"):
    """Search for papers by calling retrieval API"""
    import httpx
    
    url = "http://120.92.112.87:25620/api/api/retrieval/retrieve"
    data = {
        "queries": [query],
        "topk": 50,
        # "embedding_threshold": 0.5,
        # "knn_candidate_num": 100,
        # "return_scores": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract and format the results
            formatted_results = []
            if result.get("status") == "success":
                for item in result["result"]:
                    authors = item.get("authors", [])
                    if authors:
                        authors_str = ", ".join([author.get("name", "") for author in authors])
                    else:
                        authors_str = ""
                    formatted_item = {
                        "title": item.get("title", ""),
                        "abs": item.get("abstract", ""),
                        # "abs": item.get("tldr", ""),
                        "authors": authors_str,
                        "orgs": "",
                        "url": item.get("urls", ""),
                        "meta": ""
                    }
                    formatted_results.append(formatted_item)
            return formatted_results
            
    except Exception as e:
        # Fallback to test data if API call fails
        print(f"Error in search: {e}")
        return load_json("data/test_data.json") * 5

# @app.get("/api/deep_search")
# async def deep_search(query: str = "Agentic Reinforcement Learning"):
#     import httpx
    
#     url = "http://120.92.112.87:25620/api/api/search/fast_search"
#     data = {
#         "query": query,
#     }
    
#     try:
#         async with httpx.AsyncClient(timeout=120.0) as client:
#             response = await client.post(url, json=data)
#             response.raise_for_status()
#             result = response.json()
            
#             # Extract and format the results
#             formatted_results = []
#             if result.get("status") == "success":
#                 for item in result["result"]:
#                     authors = item.get("authors", [])
#                     if authors:
#                         authors_str = ", ".join([author.get("name", "") for author in authors])
#                     else:
#                         authors_str = ""
#                     formatted_item = {
#                         "title": item.get("title", ""),
#                         "abs": item.get("abstract", ""),
#                         # "abs": item.get("tldr", ""),
#                         "authors": authors_str,
#                         "orgs": "",
#                         "url": item.get("urls", ""),
#                         "meta": f"Relevance: {item.get('score', '0.0'):.3f}"
#                     }
#                     formatted_results.append(formatted_item)
#             return formatted_results
            
#     except Exception as e:
#         # Log the error
#         print(f"Error in deep_search: {e}")
#         # Fallback to test data if API call fails
#         return load_json("data/test_data.json") * 5

@app.get("/api/deep_search")
async def deep_search(
    query: str = "Agentic Reinforcement Learning", 
):
    import httpx

    url = "http://120.92.112.87:25620/api/api/retrieval_for_test/search"
    search_funcs = []

    query_rewrite = False
    coarse_rerank = True
    fine_rerank = True
    metadata = True
    introduction = True
    section = True
    roc = True

    if metadata: search_funcs.append("metadata")
    if introduction: search_funcs.append("introduction")
    if section: search_funcs.append("section")
    if roc: search_funcs.append("roc")
        
    data = {
        "queries": [query],
        "use_query_decomposition": query_rewrite,
        "use_coarse_rerank": coarse_rerank,
        "use_fine_rerank": fine_rerank,
        "search_funcs": search_funcs,
    }
    print(data)
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            result = response.json()[0]
            
            # Extract and format the results
            formatted_results = []
            if result.get("status") == "success":
                for item in result["result"]:
                    authors = item.get("authors", [])
                    if authors:
                        authors_str = ", ".join([author.get("name", "") for author in authors])
                    else:
                        authors_str = ""
                    formatted_item = {
                        "title": item.get("title", ""),
                        # "abs": item.get("abstract", ""),
                        "abs": item.get("tldr", ""),
                        "authors": authors_str,
                        "orgs": "",
                        "url": item.get("urls", ""),
                        "meta": f"Relevance: {item.get('score', '0.0'):.3f}"
                    }
                    formatted_results.append(formatted_item)
            return formatted_results
            
    except Exception as e:
        # Log the error
        print(f"Error in deep_search: {e}")
        # Fallback to test data if API call fails
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
