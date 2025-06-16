#!/bin/bash
# Run ILRI document instance alongside main instance

echo "Starting ILRI document processing instance..."
echo "This will run on different ports to avoid conflicts:"
echo "- Database: localhost:5434"
echo "- API: localhost:8001" 
echo "- Frontend: localhost:8081"
echo "- Ingestion: localhost:5051"

# Start the ILRI instance
docker compose -f docker-compose.ilri.yml up -d

echo ""
echo "Services starting up..."
echo "Check status with: docker compose -f docker-compose.ilri.yml ps"
echo "View logs with: docker compose -f docker-compose.ilri.yml logs -f"
echo ""
echo "Access points:"
echo "- Frontend: http://localhost:8081"
echo "- API: http://localhost:8001"
echo "- Health check: curl http://localhost:8001/health"
echo ""
echo "To stop: docker compose -f docker-compose.ilri.yml down"