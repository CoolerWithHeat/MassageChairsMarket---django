#!/bin/bash

# Navigate to the project directory
cd /home/badassguy/Desktop/dropshipper-store || { echo "Directory not found"; exit 1; }

# Create a virtual environment in the 'env' directory (if it doesn't already exist)
if [ ! -d "env" ]; then
    python3 -m venv env
    echo "Virtual environment created."
fi

# Activate the virtual environment
source env/bin/activate

# Keep the shell active (optional)
$SHELL

