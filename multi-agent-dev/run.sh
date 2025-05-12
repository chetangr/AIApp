#!/bin/bash

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Add project directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if pip is available via the command itself or as pip3
PIP_CMD=""
if command -v pip &> /dev/null; then
    PIP_CMD="pip"
elif command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    echo "Error: Neither pip nor pip3 command found."
    exit 1
fi

# Install requirements if needed
echo "Installing required dependencies..."
$PIP_CMD install -r requirements.txt

# Run the Streamlit improved agents app
echo "Starting AI Development Team Interface..."
streamlit run app.py