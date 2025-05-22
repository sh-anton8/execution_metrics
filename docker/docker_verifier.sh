#!/bin/bash

# Function to check if the server is responsive (with timeout)
check_server() {
  curl --silent --show-error --max-time 80 --connect-timeout 70 http://localhost:1337/health | grep -q "ok"
  return $?
}

# Function to restart the Docker container
restart_container() {
  echo "Stopping container..."
  docker stop code-execution-api >/dev/null 2>&1
  docker rm code-execution-api >/dev/null 2>&1
  echo "Starting container..."
  docker run -d --name code-execution-api -p 1337:1337 code-execution-api
}

# Main loop
while true; do
  echo "Check server"
  if ! check_server; then
    echo "Server is unresponsive or timed out. Restarting container..."
    restart_container
  fi
  sleep 10
done
