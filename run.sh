# !/bin/sh
PID_FILE="app_pid.txt"
LOG_DIRECTORY="logs"

set -e

# this will create venv from python version defined in .python-version
if [ ! -d .venv ]; then
  uv venv
fi

# Activate the virtual environment using the dot command
. .venv/bin/activate

# install requirements for the project
uv pip install --upgrade -r requirements.txt --quiet

log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check the operating system
check_os() {
    case "$OSTYPE" in
        darwin*) 
            log_message "✅ macOS detected. Proceeding with installation..."
            OS="macos"
            ;;
        linux*)
            log_message "✅ Linux detected. Proceeding with installation..."
            OS="linux"
            ;;
        *)
            log_message "❌ Unsupported operating system: $OSTYPE"
            exit 1
            ;;
    esac
}

# Function to check if Ollama is already installed
check_ollama_installed() {
    if command -v ollama &>/dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to check if Homebrew is installed (for macOS)
check_homebrew() {
    if ! command -v brew &>/dev/null; then
        log_message "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        log_message "✅ Homebrew is already installed."
    fi
}

# Function to install Ollama on macOS
install_ollama_macos() {
    log_message "🚀 Installing Ollama on macOS..."
    brew update
    brew install ollama
}

# Function to install Ollama on Linux
install_ollama_linux() {
    log_message "🚀 Installing Ollama on Linux..."
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
}

# Function to check if Ollama is installed
check_ollama() {
    if command -v ollama &>/dev/null; then
        log_message "✅ Ollama is installed. Version:"
    else
        log_message "❌ Failed to install Ollama. Please check your system configuration."
        exit 1
    fi
}

is_ollama_running() {
    if command -v netstat >/dev/null; then
        if netstat -tuln 2>/dev/null | grep -q ":11434 "; then
            return 0
        fi
    fi

    return 1
}

# Main installation steps
log_message "Starting Ollama installation..."

# Step 1: Check the operating system
check_os

# Step 2: Perform installation based on OS
installed_flag=check_ollama_installed;

if [[ "$OS" == "macos" && $installed_flag -eq 0 ]]; then
    check_homebrew
    install_ollama_macos
elif [[ "$OS" == "linux" && $installed_flag -eq 0 ]]; then
    install_ollama_linux
else
    log_message "✅ Ollama is already installed. Version:"
    ollama --version
fi


# Step 3: Check Ollama service status
log_message "Checking Ollama service status..."

if is_ollama_running; then
    log_message "Ollama is already running"
else
    log_message "Ollama is not running. Starting Ollama..."
    if command -v ollama >/dev/null; then
        nohup ollama serve > logs/ollama_serve.log 2>&1 & 
        sleep 2  # Give it a moment to start
        
        if check_ollama; then
            log_message "✅ Ollama started successfully"
        else
            log_message "❌ Error: Failed to start Ollama"
            exit 1
        fi
    else
        log_message "❌ Error: Ollama is not installed"
        exit 1
    fi
fi

log_message "🎉 Ollama installation complete!"

# install ollama models  (suggested options)
# ollama pull qwen2:1.5b 
# ollama pull qwen2.5:1.5b # best larger model
ollama pull qwen2.5:0.5b  # default model
# ollama pull smollm2:135m
# ollama pull smollm2:360m
# ollama pull tinyllama
# ollama pull tinydolphin
# ollama pull granite3-moe

# Output Python version
log_message "Running fed_rag with $(python3 --version) at '$(which python3)'"

is_gradio_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null; then
            if curl -s http://localhost:7861 > /dev/null; then
                return 0
            fi
        fi
    fi
    
    # Also check if port is in use by any process
    if lsof -i:7861 > /dev/null 2>&1; then
        return 1
    fi
    
    return 1 
}

start_gradio() {
    log_message "Starting Gradio application..."
    
    nohup python3 app.py > "logs/app.log" 2>&1 &
    APP_PID=$!
    echo "$APP_PID" > "$PID_FILE"
    
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:7861 > /dev/null; then
            log_message "✅ Gradio app started successfully! (PID: $APP_PID) Go to: http://localhost:7861"
            return 0
        fi
    done
    
    log_message "❌ Failed to start Gradio app. Check logs at $APP_LOG"
    rm -f "$PID_FILE"
    return 1
}

if is_gradio_running; then
    log_message "Gradio app is already running"
    if [ -f "$PID_FILE" ]; then
        log_message "PID: $(cat "$PID_FILE")"
    else
        log_message "PID file not found, but port 7861 is in use"
    fi
else
    rm -f "$PID_FILE"
    start_gradio
fi

# Run the index updater every 5 mins
python3 index_updater.py > "logs/index_updater.log" 2>&1 &

# deactivate the virtual environment
deactivate