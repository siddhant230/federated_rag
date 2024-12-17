#!/bin/sh

set -e

# this will create venv from python version defined in .python-version
if [ ! -d .venv ]; then
  uv venv
fi

# Activate the virtual environment using the dot command
. .venv/bin/activate

# install requirements for the project
uv pip install --upgrade -r requirements.txt --quiet

# setup ollama
# Check if Ollama is installed
if command -v ollama &> /dev/null; then
  echo "Ollama is already installed."
else
  echo "Ollama is not installed. Installing..."
  # Download and run the Ollama install script
  curl -fsSL https://ollama.com/install.sh | sh
  echo "Ollama installed successfully."
fi

# install ollama qwen2:1.5b
ollama pull qwen2:1.5b # default model

# run app using python from venv
echo "Running fed_rag UI with $(python3 --version) at '$(which python3)'"
python3 app.py

# deactivate the virtual environment
deactivate
