.PHONY: help build up down logs shell test clean

# Default target
help:
	@echo "Dynamic DCA Docker Commands:"
	@echo ""
	@echo "  make build    - Build the Docker image"
	@echo "  make up       - Start the service in background"
	@echo "  make down     - Stop the service"
	@echo "  make logs     - View service logs"
	@echo "  make shell    - Access container shell"
	@echo "  make test     - Run strategy once for testing"
	@echo "  make clean    - Remove containers and images"
	@echo "  make restart  - Restart the service"
	@echo ""
	@echo "Before first run:"
	@echo "  cp env.example .env"
	@echo "  # Edit .env with your configuration"

# Build the Docker image
build:
	docker-compose build

# Start the service
up:
	docker-compose up -d

# Stop the service
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f dynamic-dca

# Access container shell
shell:
	docker-compose exec dynamic-dca bash

# Run strategy once for testing (bypasses cron)
test:
	docker-compose run --rm dynamic-dca python dynamic_dca.py

# Clean up containers and images
clean:
	docker-compose down --rmi all --volumes --remove-orphans

# Restart the service
restart: down up

# Rebuild and restart
rebuild: clean build up
