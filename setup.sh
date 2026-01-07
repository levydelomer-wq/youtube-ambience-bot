#!/bin/bash
set -e

echo "=== YouTube Ambience Bot Setup ==="

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    sudo apt-get update && sudo apt-get install -y ffmpeg
else
    echo "ffmpeg already installed"
fi

# Install Real-ESRGAN
if ! command -v realesrgan-ncnn-vulkan &> /dev/null; then
    echo "Installing Real-ESRGAN..."
    mkdir -p ~/.local/bin ~/.local/share/realesrgan

    cd /tmp
    wget -q https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip -O realesrgan.zip
    unzip -q -o realesrgan.zip -d realesrgan

    cp realesrgan/realesrgan-ncnn-vulkan ~/.local/bin/
    chmod +x ~/.local/bin/realesrgan-ncnn-vulkan
    cp -r realesrgan/models ~/.local/share/realesrgan/

    rm -rf realesrgan realesrgan.zip
    cd -

    # Add to PATH if not already there
    if ! echo "$PATH" | grep -q ".local/bin"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
    fi

    echo "Real-ESRGAN installed"
else
    echo "Real-ESRGAN already installed"
fi

echo ""
echo "=== Setup Complete ==="
echo "Activate the environment with: source venv/bin/activate"
