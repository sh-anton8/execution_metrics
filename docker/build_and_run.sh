#!/bin/bash

echo "Building Docker image..."
docker build -t code-execution-api .
echo "Starting container..."
docker run --name code-execution-api -p 1337:1337 code-execution-api 