# !/bin/sh

set -e

# this will create venv from python version defined in .python-version
if [ ! -d .venv ]; then
  uv venv
fi

# Activate the virtual environment using the dot command
. .venv/bin/activate

# install requirements for the project
uv pip install --upgrade -r requirements.txt --quiet

# Function to check the operating system
check_os() {
    case "$OSTYPE" in
        darwin*) 
            echo "✅ macOS detected. Proceeding with installation..."
            OS="macos"
            ;;
        linux*)
            echo "✅ Linux detected. Proceeding with installation..."
            OS="linux"
            ;;
        *)
            echo "❌ Unsupported operating system: $OSTYPE"
            exit 1
            ;;
    esac
}

# Function to check if Ollama is already installed
check_ollama_installed() {
    if command -v ollama &>/dev/null; then
        echo "✅ Ollama is already installed. Version:"
        ollama --version
        return 1
    else
        echo "ℹ️ Ollama is not installed. Proceeding with installation..."
        return 0
    fi
}

# Function to check if Homebrew is installed (for macOS)
check_homebrew() {
    if ! command -v brew &>/dev/null; then
        echo "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✅ Homebrew is already installed."
    fi
}

# Function to install Ollama on macOS
install_ollama_macos() {
    echo "🚀 Installing Ollama on macOS..."
    brew update
    brew install ollama
}

# Function to install Ollama on Linux
install_ollama_linux() {
    echo "🚀 Installing Ollama on Linux..."
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
}

# Function to check if Ollama is installed
check_ollama() {
    if command -v ollama &>/dev/null; then
        echo "✅ Ollama installed successfully!"
        ollama --version
    else
        echo "❌ Failed to install Ollama. Please check your system configuration."
        exit 1
    fi
}

# Main installation steps
echo "Starting Ollama installation..."

# Step 1: Check the operating system
check_os

# Step 2: Perform installation based on OS
if [[ "$OS" == "macos" && $(check_ollama_installed) == 1 ]]; then
    check_homebrew
    install_ollama_macos
elif [[ "$OS" == "linux" && $(check_ollama_installed) == 1 ]]; then
    install_ollama_linux
fi

# Step 3: Verify Ollama installation
check_ollama

echo "🎉 Ollama installation complete!"

# install ollama models  (suggested options)
# ollama pull qwen2:1.5b 
# ollama pull qwen2.5:1.5b # best larger model
ollama pull qwen2.5:0.5b  # default model
# ollama pull smollm2:135m
# ollama pull smollm2:360m
# ollama pull tinyllama
# ollama pull tinydolphin
# ollama pull granite3-moe

# run app using python from venv
echo "Running fed_rag UI with $(python3 --version) at '$(which python3)'"
python3 app.py

# deactivate the virtual environment
deactivate
