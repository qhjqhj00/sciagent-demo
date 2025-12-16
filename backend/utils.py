import json
import time
import random
from pydantic import BaseModel
from openai import OpenAI

def get_agent(base_url, api_key):
    llm = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    return llm

def stream_completion(
    agent, model_name, prompt, stop=None, stream=True, schema: BaseModel = None, max_tokens: int = 60000, top_p: float = 0.8, temperature: float = 0.8, repetition_penalty: float = 1.05, min_p: float = 0.05, top_k: int = 20):
    
    num_try = 0
    while num_try < 5:
        try:
            response = agent.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                top_p=top_p,
                temperature=temperature,
                stream=stream,
                stop=stop,
                extra_body={
                    "min_p": min_p,
                    "repetition_penalty": repetition_penalty,
                    'include_stop_str_in_output': True,
                    'top_k': top_k,
                    "guided_json": schema.model_json_schema() if schema else None,
                }
            )
            break
        except Exception as e:
            print(f"Error: {e}")
            num_try += 1
            time.sleep(1)

    if stream:
        response_content = ""   
        for chunk in response:
            response_content += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end="", flush=True)
        return response_content
    else:
        return response.choices[0].message.content

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_jsonl(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def save_jsonl(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def load_txt(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()