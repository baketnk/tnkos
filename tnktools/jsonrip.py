

import os
import subprocess
import json
import yaml
from collections import defaultdict

class FileCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size

    def get(self, file_path):
        return self.cache.get(file_path)

    def set(self, file_path, value):
        if len(self.cache) >= self.max_size:
            # Remove the oldest item if cache is full
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[file_path] = value

    def clear(self):
        self.cache.clear()

file_cache = FileCache()

def search_properties(directory, pattern):
    results = []
    file_cache.clear()  # Clear cache before each search

    # Run ripgrep to find matches
    rg_command = f"rg --json {pattern} {directory}"
    rg_output = subprocess.run(rg_command, shell=True, capture_output=True, text=True)

    if rg_output.returncode != 0 and rg_output.returncode != 1:
        raise Exception(f"ripgrep error: {rg_output.stderr}")

    # Group matches by file
    file_matches = defaultdict(list)
    for line in rg_output.stdout.splitlines():
        match_data = json.loads(line)
        if match_data['type'] == 'match':
            file_path = match_data['data']['path']['text']
            line_number = match_data['data']['line_number']
            file_matches[file_path].append(line_number)

    # Process matches
    for file_path, line_numbers in file_matches.items():
        if file_path.endswith('.json'):
            results.extend(process_json_file(file_path, pattern))
        elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
            results.extend(process_yaml_file(file_path, pattern))

    return results

def process_json_file(file_path, pattern):
    cached_results = file_cache.get(file_path)
    if cached_results is not None:
        return cached_results

    jq_command = f"jq -c 'paths(select(tostring | test(\"{pattern}\"))) as $p | $p + [getpath($p)] | {{key: $p[:-1] | join(\".\"), value: .[-1]}}' {file_path}"
    jq_output = subprocess.run(jq_command, shell=True, capture_output=True, text=True)
    
    if jq_output.returncode != 0:
        raise Exception(f"jq error: {jq_output.stderr}")

    results = []
    for line in jq_output.stdout.splitlines():
        match = json.loads(line)
        key = f"{file_path}:{match['key']}"
        value = str(match['value'])
        if len(value) > 256:
            value = value[:253] + "..."
        results.append((key, value))

    file_cache.set(file_path, results)
    return results

def process_yaml_file(file_path, pattern):
    cached_results = file_cache.get(file_path)
    if cached_results is not None:
        return cached_results

    yq_command = f"yq -o=json '.. | select(has(\"{pattern}\")) | {{key: path | join(\".\"), value: .[\"{pattern}\"]}}' {file_path}"
    yq_output = subprocess.run(yq_command, shell=True, capture_output=True, text=True)
    
    if yq_output.returncode != 0:
        raise Exception(f"yq error: {yq_output.stderr}")

    results = []
    for line in yq_output.stdout.splitlines():
        match = json.loads(line)
        key = f"{file_path}:{match['key']}"
        value = str(match['value'])
        if len(value) > 256:
            value = value[:253] + "..."
        results.append((key, value))

    file_cache.set(file_path, results)
    return results

# Example usage
if __name__ == "__main__":
    directory = "/path/to/search/directory"
    pattern = "search_pattern"
    
    try:
        matches = search_properties(directory, pattern)
        for key, value in matches:
            print(f'"{key}": {value}')
    except Exception as e:
        print(f"Error: {str(e)}")
