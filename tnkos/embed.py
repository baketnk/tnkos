import os
import json
import httpx

class Embedder:
    EMBEDDING_MODEL = "embedding-model-name"
    EMBED_ENDPOINT = "/api/embed"
    
    def __init__(self):
        self.EMBED_API_URL = os.getenv("EMBED_API_URL", "http://localhost:11434")

    def embed(self, input: str) -> dict:
        headers = {
            "Content-Type": "application/json",
        }

        data = {
            "model": self.EMBEDDING_MODEL,
            "input": input
        }

        with httpx.Client() as client:
            response = client.post(self.EMBED_API_URL + self.EMBED_ENDPOINT, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
