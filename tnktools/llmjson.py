import json
import re

def parse_llm_json(json_string: str) -> dict:
    """
    Parse JSON string from LLM output, handling potential formatting issues.
    
    Args:
    json_string (str): The JSON string to parse, potentially malformed.
    
    Returns:
    dict: Parsed JSON data, or None if parsing fails.
    """
    # Remove any leading/trailing backticks and 'json' keyword
    json_string = json_string.split('```json')[-1]

    
    # Replace escaped newlines with spaces
    json_string = re.sub(r'\\{1,2}n', ' ', json_string)
    
    try:
        # Attempt to parse the JSON string directly
        print(f"attempt 1 {json_string}")
        return json.loads(json_string)
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract JSON-like content
        json_match = re.search(r'\{.*\}', json_string, re.DOTALL)
        print(json_match)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                print(f"Failed to parse JSON. Raw output: {json_string}")
                return None
        else:
            print(f"Failed to extract JSON content. Raw output: {json_string}")
            return None


