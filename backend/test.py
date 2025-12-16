import requests

def local_search(queries):
    """
    Use local Elasticsearch service to search for papers
    
    Args:
        queries: A list of queries to search for.
    
    Returns:
        list[dict]: A flattened list containing all query results.
    """
    url, params = "http://120.92.112.87:25620/es/retrieve", {"index": "papers"}
    payload = {
        "queries": queries,
        "topk": 10,
        "return_scores": True
    }

    try:
        response = requests.post(url, params=params, json=payload, timeout=5)
        response.raise_for_status() 
        data = response.json()
        if data.get("status") != "success":
            print(f"❌ retrieval failed: {data.get('status')}")
            return []
        all_results = data['result']
        print(f"✅ retrieval success, totally {len(all_results)} results returned")
        return all_results
    except requests.exceptions.RequestException as e:
        print(f"❌ requests failed: {e}")
        return []
    
if __name__ == "__main__":
    queries = ["deep learning"]
    results = local_search(queries)
    print(results)