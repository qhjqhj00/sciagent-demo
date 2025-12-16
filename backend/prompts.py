from pydantic import BaseModel, Field

class QueryExpansionResponse(BaseModel):
    expanded_queries: list[str] = Field(description="A list of expanded queries")

QUERY_EXPANSION_PROMPT = """You are an expert at expanding search queries to improve information retrieval. Given a user's query, generate multiple related queries that capture different aspects, synonyms, and related concepts to maximize retrieval recall.

Instructions:
1. Generate 3-5 expanded queries based on the input query
2. Include synonyms, related terms, and different phrasings
3. Consider both broader and more specific variations
4. Maintain the core intent of the original query
5. Output the result in JSON format

Input Query: {query}

Output the expanded queries in the following JSON format:
{{
    "expanded_queries": {{
        "expanded query 1",
        "expanded query 2", 
        "expanded query 3"
    }}
}}"""

if __name__ == "__main__":
    from utils import *
    api_dict = load_json("data/api.json")
    agent = get_agent(api_dict["openrouter"]["url"], api_dict["openrouter"]["api_key"])
    query = "deep learning"
    prompt = QUERY_EXPANSION_PROMPT.format(query=query)
    response = stream_completion(agent, "gpt-4o-mini", prompt, schema=QueryExpansionResponse)
    print(response.expanded_queries)