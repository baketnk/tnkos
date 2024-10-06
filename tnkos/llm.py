import os
import json
import httpx
from typing import Dict, List, Union, Generator

class LLM:
    DEFAULT_MODEL = os.getenv("TNKOS_MODEL", "llama3.2:3b-instruct-fp16")
    DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"

    
    OPENAI_API_URL = os.getenv("TNKOS_URL", "http://localhost:11434/v1")
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self):
        self.prompts = {}
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


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
        options.setdefault("model", self.DEFAULT_ANTHROPIC_MODEL if options.get("anthropic", False) else self.DEFAULT_MODEL)
        try:
            del options["anthropic"]
        except:
            pass
        if options["model"].startswith("claude-"): 
            return self._anthropic_call(messages, options)
        else:
            return self._openai_call(messages, options)

    def llm_stream(self, messages: List[Dict[str, str]], options: Dict = {}) -> Generator[str, None, None]:
        options["stream"] = True
        options.setdefault("model", self.DEFAULT_ANTHROPIC_MODEL if options.get("anthropic", False) else self.DEFAULT_MODEL)
        try:
            del options["anthropic"]
        except:
            pass
        if self.DEFAULT_MODEL.startswith("claude-"):
            return self._anthropic_stream(messages, options)
        else:
            return self._openai_stream(messages, options)
    
    def _openai_call(self, messages: List[Dict[str, str]], options: Dict) -> str:
        headers = {
            "Content-Type": "application/json",
        }
        if self.OPENAI_API_KEY:
            headers["Authorization"] = f"Bearer {self.OPENAI_API_KEY}"

        data = {
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
        }
        if self.OPENAI_API_KEY:
            headers["Authorization"] = f"Bearer {self.OPENAI_API_KEY}"

        data = {
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
            "anthropic-version": "2023-06-01",
            "X-API-Key": self.ANTHROPIC_API_KEY
        }
        data = {
            "messages": messages,
            "max_tokens": options.get("max_tokens", 1000),
            **options
        }
        with httpx.Client() as client:
            response = client.post(self.ANTHROPIC_API_URL, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            return response.json()["content"][0]["text"]

    def _anthropic_stream(self, messages: List[Dict[str, str]], options: Dict) -> Generator[str, None, None]:
        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "X-API-Key": self.ANTHROPIC_API_KEY
        }
        data = {
            "messages": messages,
            "max_tokens": options.get("max_tokens", 1000),
            "stream": True,
            **options
        }
        with httpx.Client() as client:
            with client.stream("POST", self.ANTHROPIC_API_URL, headers=headers, json=data, timeout=30.0) as response:
                for line in response.iter_lines():
                    if line:
                        try:
                            json_line = json.loads(line)
                            if json_line["event"] == "content_block_delta":
                                yield json_line["delta"]["text"]
                        except:
                            pass

    def get_prompt(self, prompt_name: str) -> str:
        if prompt_name not in self.prompts:
            prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", f"{prompt_name}.txt")
            with open(prompt_path, "r") as f:
                self.prompts[prompt_name] = f.read().strip()
        return self.prompts[prompt_name]
