.PHONY: all start stop test integration clean

# Do the full integration run
all: integration

# Start API container using Docker
start:
	@./scripts/build.sh

# Stop API container
stop:
	@./scripts/stop_server.sh

# Run the Python integration test
test:
	@./scripts/run_integration_test.sh

# Run the Python benchmark test
benchmark:
	@./scripts/run_bechmark_test.sh

# Full integration test: build + run + test + stop
integration:
	@./scripts/run_integration_test.sh

# Clean unused Docker resources
clean:
	@docker system prune -f
