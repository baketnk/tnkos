#!/bin/bash

# Configuration
PROJECT_ROOT="$HOME/workspace/tnkos" # Update this to your project root path
VENV_PATH="$PROJECT_ROOT/.venv"
TNKTOOLS_PACKAGE="tnktools"
TNKTOOLS_PREFIX="tnk"
PYTHON_CMD="python3"

# Function to add source command to shell RC file
add_to_shell_rc() {
  local rc_file=""
  local shell_name=""

  # Determine the shell and RC file
  if [ -n "$ZSH_VERSION" ]; then
    rc_file="$HOME/.zshrc"
    shell_name="zsh"
  elif [ -n "$BASH_VERSION" ]; then
    rc_file="$HOME/.bashrc"
    shell_name="bash"
  else
    echo "Unsupported shell. Please manually add the source command to your shell's RC file."
    return 1
  fi

  # Check if the source command already exists in the RC file
  if grep -q "source $PROJECT_ROOT/toolsrc.sh" "$rc_file"; then
    echo "Source command already exists in $rc_file"
    return 0
  fi

  # Add the source command to the RC file
  echo "" >>"$rc_file"
  echo "# Source tnktools" >>"$rc_file"
  echo "source $PROJECT_ROOT/toolsrc.sh" >>"$rc_file"

  echo "Added source command to $rc_file"
  echo "Please restart your $shell_name session or run 'source $rc_file' to apply changes."
  return 0
}

# Function to discover tnktools modules
discover_modules() {
  $PYTHON_CMD -c "
import importlib.util
import pkgutil
import os
import sys

# Add the project root to the Python path
project_root = '$PROJECT_ROOT'
sys.path.insert(0, project_root)

modules = []
tnktools_path = os.path.join(project_root, '$TNKTOOLS_PACKAGE')

if not os.path.isdir(tnktools_path):
    print(f'Error: {tnktools_path} is not a directory', file=sys.stderr)
    sys.exit(1)

try:
    # Try to import the tnktools package
    import tnktools
except ImportError:
    print(f'Error: Unable to import tnktools package. Make sure it is installed.', file=sys.stderr)
    sys.exit(1)

for item in os.listdir(tnktools_path):
    if item.endswith('.py') and item != '__init__.py':
        module_name = item[:-3]  # Remove .py extension
        if importlib.util.find_spec(f'$TNKTOOLS_PACKAGE.{module_name}'):
            modules.append(module_name)

if not modules:
    print('No tnktools modules found.', file=sys.stderr)
    sys.exit(1)

print(' '.join(modules))
  "
}

# Function to run tnktools modules
run_tnktools() {
  local module=$1
  shift # Remove the first argument (module name) from the argument list

  # Check if the module name is a command
  if ! command -v "$module" &>/dev/null; then
    module="${TNKTOOLS_PREFIX}${module}"
  fi

  # Run the Python script with the module name and remaining arguments
  source "$VENV_PATH/bin/activate"
  cd "$PROJECT_ROOT"
  PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH" $PYTHON_CMD -m ${TNKTOOLS_PACKAGE}."$module" "$@"
  deactivate
}

# Check if the add-to-rc command is given
if [ "$1" = "add-to-rc" ]; then
  add_to_shell_rc
  exit $?
fi

# Generate aliases for all discovered modules
for module in $(discover_modules); do
  alias $module="run_tnktools $module"
done

# Optional: Print available commands
echo "Available tnktools commands: $(alias | grep "run_tnktools" | sed 's/alias \(.*\)=.*/\1/' | tr '\n' ' ')"
