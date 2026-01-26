#!/bin/bash
set -e

# Build + launch API
./scripts/build.sh

# Run test
echo "Running integration test..."
python tests/test_api_integration.py

# Shutdown container
./scripts/stop_server.sh

echo "Integration test run complete."