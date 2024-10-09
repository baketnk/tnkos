# tnkos/suggestions.py

import asyncio
from functools import lru_cache
from .llm import LLM
import os

llm = LLM()

@lru_cache(maxsize=100)
def get_cached_suggestions(input_prefix, current_dir, history):
    # This function will cache results based on the input parameters
    return llm.prompt_call("shell_suggestions", 
                           input_prefix=input_prefix, 
                           current_dir=current_dir, 
                           history=history)

async def get_suggestions_async(current_input, current_dir, history):
    # Simulate an asynchronous operation
    await asyncio.sleep(0.1)
    
    # Convert history list to a string
    history_str = "\n".join(history[-5:])  # Use last 5 commands for context
    
    # Get suggestions from LLM (using cache)
    suggestions_str = get_cached_suggestions(current_input[:10], current_dir, history_str)
    
    # Parse suggestions string into a list
    suggestions = [s.strip() for s in suggestions_str.split(',') if s.strip()]
    
    return suggestions[:3]  # Limit to 3 suggestions
