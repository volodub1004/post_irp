#!/bin/bash
set -e

# Build + launch API
./scripts/build.sh

# Run test
echo "Running benchmark test..."
python tests/test_benchmark_api_with_verification.py

# Shutdown container
./scripts/stop_server.sh

echo "Benchmark test run complete."