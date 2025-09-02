#!/usr/bin/env bash

set -euo pipefail

echo "Starting ILRI document processing instance..."
echo "This will run on different ports to avoid conflicts:"
echo "- Database: localhost:5434"
echo "- API: localhost:8001" 
echo "- Ingestion: localhost:5051"
echo "- GROBID: localhost:8070"

docker compose -f docker-compose.yml up -d

# Helpful checks
echo ""
echo "Services starting up..."
echo "Check status with: docker compose -f docker-compose.yml ps"
echo "View logs with: docker compose -f docker-compose.yml logs -f"
echo ""
echo "Access points:"
echo "- API: http://localhost:8001"
echo "- Health check: curl http://localhost:8001/health"
echo "- GROBID UI: http://localhost:8070"
echo ""
echo "To stop: docker compose -f docker-compose.yml down"
