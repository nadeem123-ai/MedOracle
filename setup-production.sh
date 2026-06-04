#!/bin/bash
# MedOracle  Production Setup Script
# Automates environment setup, database initialization, and service startup

set -e

echo "════════════════════════════════════════════════════════════"
echo "  MedOracle  - Production Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "1️⃣  Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found. Please install Docker.${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose not found. Please install Docker Compose.${NC}"; exit 1; }
echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Check environment file
echo "2️⃣  Setting up environment variables..."
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    if [ ! -f .env.example ]; then
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and set your GROQ_API_KEY and other variables${NC}"
    echo "   nano .env"
    exit 0
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi
echo ""

# Generate secret key if needed
echo "3️⃣  Validating security configuration..."
if grep -q "SECRET_KEY=your-secret-key" .env; then
    echo -e "${YELLOW}⚠ Generating random SECRET_KEY...${NC}"
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s|SECRET_KEY=your-secret-key|SECRET_KEY=$SECRET|g" .env
    echo -e "${GREEN}✓ SECRET_KEY generated and saved${NC}"
fi
echo ""

# Check API key
echo "4️⃣  Checking API keys..."
if grep -q "GROQ_API_KEY=your-groq-api-key" .env; then
    echo -e "${RED}✗ GROQ_API_KEY not configured${NC}"
    echo "   Please set your Groq API key in .env"
    exit 1
else
    echo -e "${GREEN}✓ GROQ_API_KEY configured${NC}"
fi
echo ""

# Build images
echo "5️⃣  Building Docker images..."
docker-compose build --quiet
echo -e "${GREEN}✓ Docker images built${NC}"
echo ""

# Start services
echo "6️⃣  Starting services..."
docker-compose up -d
echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Wait for services to be healthy
echo "7️⃣  Waiting for services to be ready..."
max_attempts=30
attempt=0

until curl -s http://localhost:8000/health >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        echo -e "${RED}✗ API failed to start${NC}"
        docker-compose logs api
        exit 1
    fi
    echo -n "."
    sleep 2
done

echo ""
echo -e "${GREEN}✓ API is ready${NC}"
echo ""

# Run database migrations
echo "8️⃣  Initializing database..."
docker-compose exec -T api python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Print access information
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📍 Service URLs:"
echo "   • Streamlit UI:     http://localhost:8501"
echo "   • REST API:         http://localhost:8000"
echo "   • API Docs:         http://localhost:8000/docs"
echo "   • Database:         localhost:5432"
echo "   • Redis Cache:      localhost:6379"
echo ""
echo "🔐 Default Credentials:"
echo "   • Email: test@example.com"
echo "   • Password: demo"
echo ""
echo "📚 Documentation:"
echo "   • Architecture:     ./ARCHITECTURE.md"
echo "   • Deployment:       ./DEPLOYMENT.md"
echo "   • Checklist:        ./PRODUCTION_CHECKLIST.md"
echo "   • README:           ./README_PRODUCTION.md"
echo ""
echo "🚀 Next Steps:"
echo "   1. Log in to Streamlit UI with email: test@example.com"
echo "   2. Run a sample case analysis"
echo "   3. Check API documentation at /docs"
echo "   4. Review logs: docker-compose logs -f api"
echo ""
echo "💡 Useful Commands:"
echo "   • View logs:        docker-compose logs -f"
echo "   • Restart services: docker-compose restart"
echo "   • Stop services:    docker-compose down"
echo "   • Database shell:   docker-compose exec db psql -U MedOracle MedOracle"
echo ""
echo "════════════════════════════════════════════════════════════"
