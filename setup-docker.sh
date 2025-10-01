#!/bin/bash

set -e

echo "🚀 Dynamic DCA Docker Setup"
echo "=========================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your configuration:"
    echo "   - Add your Kraken API credentials"
    echo "   - Customize cron schedule if needed"
    echo "   - Set your timezone"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
else
    echo "✅ .env file already exists"
fi

# Create data directory
if [ ! -d data ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
    echo "✅ Created data directory"
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker-compose build

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Kraken API credentials"
echo "2. Start the service: docker-compose up -d"
echo "3. View logs: docker-compose logs -f"
echo "4. Test run: docker-compose run --rm dynamic-dca python dynamic_dca.py"
echo ""
echo "For more commands, run: make help"
