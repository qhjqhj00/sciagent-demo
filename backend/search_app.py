#!/usr/bin/env python3
"""
Simple HTTP server for serving JSON data
"""
import json
import os
import re
import hashlib
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils import *
from typing import List, Optional
import aiomysql

api_dict = load_json("data/api.json")
app = FastAPI()

CACHE_FILE = "data/cache.json"

# MySQL Database Configuration
DB_CONFIG = {
    "host": "152.136.166.243",
    "port": 25791,
    "user": "sciagent_read",
    "password": "baaiSciAgent2025@@",
    "db": "arxiv",
    "charset": "utf8mb4"
}

# Global connection pool and semaphore
db_pool = None
db_semaphore = asyncio.Semaphore(10)  # Limit concurrent database queries

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await aiomysql.create_pool(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset=DB_CONFIG["charset"],
            minsize=1,
            maxsize=10,  # Limit maximum connections
            autocommit=True
        )
    return db_pool

@app.on_event("startup")
async def startup_event():
    """Initialize connection pool on startup"""
    await get_db_pool()
    print("Database connection pool initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close connection pool on shutdown"""
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
        print("Database connection pool closed")

def load_cache():
    """Load cache from file"""
    if os.path.exists(CACHE_FILE):
        try:
            return load_json(CACHE_FILE)
        except:
            return {}
    return {}

def save_cache(cache):
    """Save cache to file"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def get_cache_key(query, query_understanding, smart_rerank, social_impact, indexing_fields):
    """Generate cache key from search parameters"""
    params_str = f"{query}|{query_understanding}|{smart_rerank}|{social_impact}|{sorted(indexing_fields)}"
    return hashlib.md5(params_str.encode()).hexdigest()

async def get_authors_from_db(arxiv_id: str) -> list:
    """Query authors from MySQL database by arxiv_id"""
    async with db_semaphore:  # Limit concurrent queries
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT authors FROM arxiv_papers WHERE arxiv_id = %s",
                        (arxiv_id,)
                    )
                    result = await cursor.fetchone()
                    if result and result[0]:
                        # Parse JSON string
                        authors_list = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                        return authors_list if isinstance(authors_list, list) else [authors_list]
        except Exception as e:
            print(f"Error fetching authors for {arxiv_id}: {e}")
        return []

async def get_venue_info_from_db(arxiv_id: str) -> dict:
    """Query venue information from MySQL database by arxiv_id"""
    async with db_semaphore:  # Limit concurrent queries
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT venue, year, misc
                        FROM proceedings_papers 
                        WHERE work_id = (
                            SELECT work_id  
                            FROM papers
                            WHERE arxiv_id = %s
                        )
                        """,
                        (arxiv_id,)
                    )
                    result = await cursor.fetchone()
                    if result:
                        return result
        except Exception as e:
            print(f"Error fetching venue info for {arxiv_id}: {e}")
        return None

async def get_social_impact_from_db(arxiv_id: str) -> dict:
    """Query social media impact from twitter_to_arxiv table in trending database"""
    async with db_semaphore:  # Limit concurrent queries
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        """
                        SELECT
                            COUNT(*) AS total_records,
                            SUM(likes) AS total_likes,
                            SUM(retweets) AS total_retweets,
                            SUM(views) AS total_views
                        FROM
                            trending.twitter_to_arxiv
                        WHERE
                            paper_id = %s
                        """,
                        (arxiv_id,)
                    )
                    result = await cursor.fetchone()
                    if result and result.get('total_records', 0) > 0:
                        return result
        except Exception as e:
            print(f"Error fetching social impact for {arxiv_id}: {e}")
        return None

def calculate_social_score(social_data: dict) -> int:
    """
    Calculate social impact score (0-100) based on likes, retweets, and views.
    Uses logarithmic scaling to handle wide range of values.
    """
    if not social_data:
        return 0
    
    likes = social_data.get('total_likes') or 0
    retweets = social_data.get('total_retweets') or 0
    views = social_data.get('total_views') or 0
    
    # Weighted scoring with logarithmic transformation
    # Weights: likes(0.3), retweets(0.4), views(0.3)
    # Retweets weighted higher as they indicate stronger engagement
    
    import math
    
    # Log transformation with base adjustment
    likes_score = math.log10(max(likes, 1)) * 10
    retweets_score = math.log10(max(retweets, 1)) * 15
    views_score = math.log10(max(views, 1)) * 8
    
    # Combine scores
    raw_score = (likes_score * 0.3 + retweets_score * 0.4 + views_score * 0.3)
    
    # Normalize to 0-100 range
    # Assumed max values: 10k likes, 5k retweets, 100k views → score ~100
    normalized_score = min(100, max(0, raw_score * 1.5))
    
    return int(normalized_score)

def format_venue_info(venue_data: dict) -> str:
    """Format venue information into a readable string"""
    if not venue_data:
        return ""
    
    parts = []
    
    # Add venue and year
    if venue_data.get('venue'):
        parts.append(venue_data['venue'])
    if venue_data.get('year'):
        parts.append(str(venue_data['year']))
    
    # Parse misc JSON
    if venue_data.get('misc'):
        try:
            misc = json.loads(venue_data['misc']) if isinstance(venue_data['misc'], str) else venue_data['misc']
            
            # Add track
            if misc.get('track'):
                track = misc['track'].title()
                parts.append(f"{track} Track")
            
            # Add paper status
            if misc.get('paper_status'):
                status = misc['paper_status'].title()
                parts.append(status)
        except Exception as e:
            print(f"Error parsing misc data: {e}")
    
    return " ".join(parts) if parts else ""

def extract_arxiv_id_from_url(url) -> str:
    """Extract arxiv_id from URL"""
    if isinstance(url, list) and url:
        url = url[0]
    if not url:
        return ""
    
    # Extract arxiv ID from URL like https://arxiv.org/pdf/2510.17431v1
    match = re.search(r'(\d{4}\.\d{5})', str(url))
    return match.group(1) if match else ""

def has_letters(text: str) -> bool:
    """Check if text contains any letters (a-z, A-Z)"""
    if not text:
        return False
    return bool(re.search(r'[a-zA-Z]', text))

def format_date(date_str: str) -> str:
    """Format ISO date string to readable format"""
    if not date_str:
        return ""
    try:
        from datetime import datetime
        # Parse ISO format: 2025-10-20T11:19:37Z
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Format as: Oct 20, 2025
        return dt.strftime("%b %d, %Y")
    except Exception as e:
        print(f"Error formatting date {date_str}: {e}")
        return ""

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


@app.get("/api/deep_search")
async def deep_search(
    query: str = "Agentic Reinforcement Learning",
    query_understanding: bool = False,
    smart_rerank: bool = True,
    use_cache: bool = False,
    social_impact: bool = False,
    indexing_fields: Optional[List[str]] = Query(None),
):
    import httpx

    # Handle indexing fields - default to all if not provided
    if indexing_fields is None or len(indexing_fields) == 0:
        indexing_fields = ['metadata', 'introduction', 'section', 'roc']
    
    # Generate cache key
    cache_key = get_cache_key(query, query_understanding, smart_rerank, social_impact, indexing_fields)
    
    # Check cache if use_cache is enabled
    if use_cache:
        cache = load_cache()
        if cache_key in cache:
            print(f"Cache hit for query: {query}")
            cached_data = cache[cache_key]
            return {
                "cache_info": "✓ Using cached result",
                "results": cached_data["results"],
                "cached_at": cached_data.get("cached_at", "")
            }
        else:
            print(f"Cache miss for query: {query}")
            cache_info = "⚠ No cache found, fetching new results..."
    else:
        cache_info = None

    url = "http://120.92.112.87:25620/api/api/retrieval_for_test/search"
    search_funcs = []

    # Map frontend parameters to backend parameters
    query_rewrite = query_understanding
    coarse_rerank = smart_rerank
    fine_rerank = smart_rerank
    
    # Map frontend field names to backend field names
    field_mapping = {
        'metadata': 'metadata',
        'introduction': 'introduction',
        'section': 'section',
        'roc': 'roc'
    }
    
    for field in indexing_fields:
        if field in field_mapping:
            search_funcs.append(field_mapping[field])
        
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
            # response = json.loads(open("/home/ubuntu/sciagent-demo/data/test_data.json").read())
            # result = response[0]
            # print(response)
            response.raise_for_status()
            result = response.json()[0]
            
            # Extract and format the results
            formatted_results = []
            if result.get("status") == "success":
                # First pass: format basic information
                for item in result["result"]:
                    authors = item.get("authors", [])
                    if authors:
                        authors_str = ", ".join([author.get("name", "") for author in authors])
                        authors_str = "" if not has_letters(authors_str) else authors_str
                        all_orgs = []
                        for author in authors:
                            all_orgs.extend(author.get("orgs", []))
                        unique_orgs = list(dict.fromkeys(all_orgs))  # 保持顺序去重
                        org_str = ", ".join(unique_orgs)
                        org_str = "" if not has_letters(org_str) else org_str
                    else:
                        authors_str = ""
                        org_str = ""
                    
                    # Extract and format date
                    dates = item.get("dates", [])
                    release_date = ""
                    if dates and len(dates) > 0:
                        release_date = format_date(dates[0])
                    
                    formatted_item = {
                        "title": item.get("title", ""),
                        "abs": item.get("tldr", ""),
                        "authors": authors_str,
                        "orgs": org_str,
                        "release_date": release_date,
                        "url": item.get("urls", ""),
                        "meta": f"Relevance: {item.get('score', '0.0'):.3f}",
                        "arxiv_id": item.get("arxiv_id", "")
                    }
                    formatted_results.append(formatted_item)
                
                # Second pass: enrich with database info using concurrent queries
                async def enrich_item(item):
                    arxiv_id = item.get("arxiv_id", "")
                    if not arxiv_id:
                        return item
                    
                    # Concurrent queries
                    # Check if authors string contains any letters
                    authors_task = get_authors_from_db(arxiv_id) if not item["authors"].strip() else None
                    venue_task = get_venue_info_from_db(arxiv_id)
                    social_task = get_social_impact_from_db(arxiv_id) if social_impact else None
                    
                    # Gather results
                    tasks = []
                    if authors_task:
                        tasks.append(authors_task)
                    tasks.append(venue_task)
                    if social_task:
                        tasks.append(social_task)
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process authors if needed
                    result_idx = 0
                    if authors_task:
                        authors_from_db = results[result_idx] if not isinstance(results[result_idx], Exception) else []
                        if authors_from_db:
                            item["authors"] = ", ".join(authors_from_db)
                        result_idx += 1
                    
                    # Process venue info
                    venue_info = results[result_idx] if not isinstance(results[result_idx], Exception) else None
                    venue_str = format_venue_info(venue_info)
                    if venue_str:
                        item["meta"] = f"{item['meta']} | {venue_str}"
                    result_idx += 1
                    
                    # Process social impact if requested
                    if social_task:
                        social_data = results[result_idx] if not isinstance(results[result_idx], Exception) else None
                        if social_data:
                            score = calculate_social_score(social_data)
                            item["social_score"] = score
                        else:
                            item["social_score"] = None
                    else:
                        item["social_score"] = None
                    
                    # Remove arxiv_id from final output
                    item.pop("arxiv_id", None)
                    return item
                
                # Enrich all items concurrently
                formatted_results = await asyncio.gather(*[enrich_item(item) for item in formatted_results])
            
            # Cache the results
            cache = load_cache()
            cache[cache_key] = {
                "query": query,
                "parameters": {
                    "query_understanding": query_understanding,
                    "smart_rerank": smart_rerank,
                    "social_impact": social_impact,
                    "indexing_fields": indexing_fields
                },
                "results": formatted_results,
                "cached_at": datetime.now().isoformat()
            }
            save_cache(cache)
            
            # Return results with cache info if applicable
            if cache_info:
                return {
                    "cache_info": cache_info,
                    "results": formatted_results
                }
            else:
                return formatted_results
            
    except Exception as e:
        # Log the error
        print(f"Error in deep_search: {e}")
        # Fallback to test data if API call fails
        fallback_results = load_json("data/test_data.json") * 5
        if cache_info:
            return {
                "cache_info": cache_info,
                "results": fallback_results
            }
        return fallback_results

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
                    "total_papers": 2905852,
                    "latest_update": "2025-12-16"
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")
                
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Database service unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=12312, log_level="info")
