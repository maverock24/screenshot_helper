#!/bin/bash

# This script automates the installation of the AI Screenshot Helper.

echo "--- AI Screenshot Helper Installer ---"
echo "This script will install system packages and Python libraries."

# --- Step 1: Install System Dependencies ---
echo ""
echo "[Step 1/4] Installing system dependencies (yad, maim, python3-venv)..."
sudo apt-get update && sudo apt-get install -y yad maim python3-venv dbus-x11
if [ $? -ne 0 ]; then
    echo "Error: Failed to install system packages. Please check your internet connection and permissions."
    exit 1
fi
echo "System dependencies installed successfully."

# --- Step 2: Create Python Virtual Environment ---
echo ""
echo "[Step 2/4] Creating Python virtual environment..."
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "Error: Failed to create Python virtual environment."
    exit 1
fi
echo "Virtual environment created."

# --- Step 3: Install Python Packages ---
echo ""
echo "[Step 3/4] Installing Python packages (google-generativeai, pillow, python-dotenv)..."
# Use the pip from the virtual environment
./.venv/bin/pip install google-generativeai pillow python-dotenv
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python packages."
    exit 1
fi
echo "Python packages installed successfully."

# --- Step 4: Configure API Key ---
echo ""
echo "[Step 4/4] Configuring Google AI API Key..."
# Prompt the user for their API key
read -p "Please enter your Google AI API Key: " API_KEY

# Create the .env file
echo "GOOGLE_API_KEY=\"$API_KEY\"" > .env
echo ".env file created successfully."

# --- Finished ---
echo ""
echo "--- Installation Complete! ---"
echo ""
echo "Your next and final step is to set a keyboard shortcut."
echo "Go to your system's Keyboard Settings and create a new custom shortcut."
echo ""
echo "Copy and paste the following full command for the shortcut:"
# Print the full, absolute path to the command
echo "  $(pwd)/.venv/bin/python $(pwd)/explain_screenshot.py"
echo ""