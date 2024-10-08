#!/bin/bash

# Define the virtual environment directory
VENV_DIR="venv"

# Create Python virtual environment if it doesn't exist and activate it
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "Virtual environment created successfully"
else
  echo "Using existing virtual environment"
fi

# Activate the virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
  echo "Activating Python virtual environment..."
  . "$VENV_DIR/bin/activate"

  if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment"
    exit 1
  fi

  echo "Virtual environment activated successfully"
else
  echo "Virtual environment activation script not found"
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --no-cache-dir -r requirements.txt

if [ $? -ne 0 ]; then
  echo "Failed to install dependencies"
  exit 1
fi

echo "Dependencies installed successfully"

# Start the Flask app in production mode with Gunicorn
echo "Starting Flask app in production mode..."
gunicorn -c gunicorn_config.py app.main:app

if [ $? -ne 0 ]; then
  echo "Failed to start Flask app in production mode"
  exit 1
fi
