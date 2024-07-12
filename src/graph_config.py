import os

def get_graph_config(model: str, key: str) -> dict: 
    return {
        "llm": {
            "api_key": key,
            "model": model,
        },
    }