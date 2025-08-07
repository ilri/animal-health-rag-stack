#!/bin/bash
# Run ILRI document instance alongside main instance (frontend is run outside Docker)

set -euo pipefail

echo "Starting ILRI document processing instance..."
echo "This will run on different ports to avoid conflicts:"
echo "- Database: localhost:5434"
echo "- API: localhost:8001" 
echo "- Ingestion: localhost:5051"
echo "- GROBID: localhost:8070"

# Start only required services: db, grobid, api, ingestion
docker compose -f docker-compose.ilri.yml up -d db-ilri grobid-ilri api-service-ilri ingestion-service-ilri

# Helpful checks
echo ""
echo "Services starting up..."
echo "Check status with: docker compose -f docker-compose.ilri.yml ps"
echo "View logs with: docker compose -f docker-compose.ilri.yml logs -f"
echo ""
echo "Access points:"
echo "- API: http://localhost:8001"
echo "- Health check: curl http://localhost:8001/health"
echo "- GROBID UI: http://localhost:8070"
echo ""
echo "To stop: docker compose -f docker-compose.ilri.yml down"