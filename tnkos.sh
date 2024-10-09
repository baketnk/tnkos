#!/bin/bash

# Resolve the script path, following symlinks
resolve_script_path() {
  local source="${BASH_SOURCE[0]}"
  local dir=""

  # Resolve $source until the file is no longer a symlink
  while [ -h "$source" ]; do
    dir="$(cd -P "$(dirname "$source")" && pwd)"
    source="$(readlink "$source")"
    # If $source was a relative symlink, we need to resolve it relative to the path where the symlink file was located
    [[ $source != /* ]] && source="$dir/$source"
  done

  echo "$(cd -P "$(dirname "$source")" && pwd)"
}

# Get the directory of this script, resolving symlinks
SCRIPT_DIR="$(resolve_script_path)"

. "$SCRIPT_DIR/.venv/bin/activate"

# Run the Python script
python3 "$SCRIPT_DIR/app.py" "$@"
