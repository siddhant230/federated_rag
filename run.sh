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
curl -fsSL https://ollama.com/install.sh | sh

# install ollama qwen2:1.5b
ollama pull qwen2:1.5b # default model

# run app using python from venv
echo "Running fed_rag UI with $(python3 --version) at '$(which python3)'"
python3 app.py

# deactivate the virtual environment
deactivate
