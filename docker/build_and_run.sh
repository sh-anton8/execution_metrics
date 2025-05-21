#!/bin/bash

echo "Building Docker image..."
docker build -t code-execution-api .
echo "Starting container..."
docker run -p 1337:1337 code-execution-api