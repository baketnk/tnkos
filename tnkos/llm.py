import os
import json
import httpx
from typing import Dict, List, Union, Generator

class LLM:
    DEFAULT_MODEL = os.getenv("TNKOS_MODEL", "llama3.2:3b-instruct-fp16")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    OPENAI_API_URL = os.getenv("TNKOS_URL", "http://localhost:11434/v1")
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/complete"

    def __init__(self):
        self.prompts = {}

    def prompt_call(self, prompt_name: str, **kwargs) -> str:
        prompt = self.get_prompt(prompt_name)
        formatted_prompt = prompt.format(**kwargs)
        messages = [{"role": "user", "content": formatted_prompt}]
        return self.llm_call(messages)

    def prompt_stream(self, prompt_name: str, **kwargs) -> Generator[str, None, None]:
        prompt = self.get_prompt(prompt_name)
        formatted_prompt = prompt.format(**kwargs)
        messages = [{"role": "user", "content": formatted_prompt}]
        return self.llm_stream(messages)

    def llm_call(self, messages: List[Dict[str, str]], options: Dict = {}) -> str:
        options["stream"] = False
        if self.DEFAULT_MODEL.startswith("gpt-"):
            return self._openai_call(messages, options)
        else:
            return self._anthropic_call(messages, options)

    def llm_stream(self, messages: List[Dict[str, str]], options: Dict = {}) -> Generator[str, None, None]:
        options["stream"] = True
        if self.DEFAULT_MODEL.startswith("gpt-"):
            return self._openai_stream(messages, options)
        else:
            return self._anthropic_stream(messages, options)

    def _openai_call(self, messages: List[Dict[str, str]], options: Dict) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_API_KEY}"
        }
        data = {
            "model": self.DEFAULT_MODEL,
            "messages": messages,
            **options
        }
        with httpx.Client() as client:
            response = client.post(self.OPENAI_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

    def _openai_stream(self, messages: List[Dict[str, str]], options: Dict) -> Generator[str, None, None]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_API_KEY}"
        }
        data = {
            "model": self.DEFAULT_MODEL,
            "messages": messages,
            "stream": True,
            **options
        }
        with httpx.Client() as client:
            with client.stream("POST", self.OPENAI_API_URL, headers=headers, json=data) as response:
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        json_line = json.loads(line[6:])
                        if json_line["choices"][0]["finish_reason"] is not None:
                            break
                        yield json_line["choices"][0]["delta"].get("content", "")

    def _anthropic_call(self, messages: List[Dict[str, str]], options: Dict) -> str:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.ANTHROPIC_API_KEY
        }
        prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
        data = {
            "model": self.DEFAULT_MODEL,
            "prompt": prompt,
            "max_tokens_to_sample": options.get("max_tokens", 1000),
            **options
        }
        with httpx.Client() as client:
            response = client.post(self.ANTHROPIC_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["completion"]

    def _anthropic_stream(self, messages: List[Dict[str, str]], options: Dict) -> Generator[str, None, None]:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.ANTHROPIC_API_KEY
        }
        prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
        data = {
            "model": self.DEFAULT_MODEL,
            "prompt": prompt,
            "max_tokens_to_sample": options.get("max_tokens", 1000),
            "stream": True,
            **options
        }
        with httpx.Client() as client:
            with client.stream("POST", self.ANTHROPIC_API_URL, headers=headers, json=data) as response:
                for line in response.iter_lines():
                    if line:
                        json_line = json.loads(line)
                        yield json_line["completion"]

    def get_prompt(self, prompt_name: str) -> str:
        if prompt_name not in self.prompts:
            prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{prompt_name}.txt")
            with open(prompt_path, "r") as f:
                self.prompts[prompt_name] = f.read().strip()
        return self.prompts[prompt_name]
