#!/bin/bash

# MathKunji - One-click launcher for macOS
# Double-click this file to build and run MathKunji

# Change to the directory where this script is located
cd "$(dirname "$0")"

echo "========================================"
echo "   MathKunji - Mathematical Solver"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running."
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Docker is running. Building and starting MathKunji via Compose..."
echo ""

# Build and start via Docker Compose
# (uses docker-compose.yml; groups the container under the project in Docker Desktop)
if ! docker compose up -d --build; then
    echo ""
    echo "ERROR: Build/start failed. Please check the error messages above."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "MathKunji is starting."
echo ""

# Wait until the app actually answers before opening the browser.
# `docker compose up -d` returns once the CONTAINER has started, not once
# Gradio is listening -- it still has to import gradio, sympy and matplotlib
# and bind the port. A fixed short sleep reliably opened the browser on a
# connection-refused page and left the user to refresh by hand.
printf "Waiting for MathKunji to respond"
for _ in $(seq 1 60); do
    if curl -s -o /dev/null "http://localhost:7860"; then
        break
    fi
    printf "."
    sleep 1
done
echo ""

# Open browser
echo ""
echo "Opening browser..."
open "http://localhost:7860"

echo ""
echo "========================================"
echo "   MathKunji is now running!"
echo "========================================"
echo ""
echo "Access the app at: http://localhost:7860"
echo ""
echo "To stop the app, use Docker Desktop or run:"
echo "  docker compose down"
echo ""
read -p "Press Enter to close this window..."
