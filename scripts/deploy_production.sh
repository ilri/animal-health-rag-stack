#!/bin/bash
#
# Production Deployment Script for Containerized RAG Starter Kit
# This script sets up nginx and systemd for production deployment
#
# Usage: sudo ./deploy_production.sh [--setup-ssl]

set -e

# Configuration
PROJECT_DIR="/home/muhia/src/containerized-rag-starter-kit"
NGINX_SITE_CONFIG="$PROJECT_DIR/deployment/nginx/ilri-archive.org"
SYSTEMD_SERVICE="$PROJECT_DIR/deployment/systemd/containerized-rag.service"
SERVER_IP="128.140.81.126"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists nginx; then
    print_error "nginx is not installed. Please install nginx first."
    exit 1
fi

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Setup nginx
print_status "Setting up nginx configuration..."

# Create nginx sites directories if they don't exist
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

# Copy nginx configuration
cp "$NGINX_SITE_CONFIG" /etc/nginx/sites-available/ilri-archive.org

# Create symbolic link
ln -sf /etc/nginx/sites-available/ilri-archive.org /etc/nginx/sites-enabled/

# Test nginx configuration
print_status "Testing nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    print_error "nginx configuration test failed"
    exit 1
fi

# SSL Setup (optional)
if [[ "$1" == "--setup-ssl" ]]; then
    print_status "Setting up self-signed SSL certificate for IP-based access..."
    
    # Create SSL directory
    mkdir -p /etc/nginx/ssl
    
    # Generate self-signed certificate
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/self-signed.key \
        -out /etc/nginx/ssl/self-signed.crt \
        -subj "/C=KE/ST=Nairobi/L=Nairobi/O=ILRI/CN=$SERVER_IP"
    
    print_status "Self-signed certificate created"
    print_warning "Note: Browsers will show a security warning for self-signed certificates"
else
    print_warning "SSL not configured. Run with --setup-ssl to set up self-signed SSL certificate"
    print_status "Site will be accessible via HTTP at http://$SERVER_IP"
fi

# Reload nginx
print_status "Reloading nginx..."
systemctl reload nginx

# Setup systemd service
print_status "Setting up systemd service..."

# Copy systemd service file
cp "$SYSTEMD_SERVICE" /etc/systemd/system/containerized-rag.service

# Adjust the service file paths if needed
sed -i "s|/home/muhia/src/containerized-rag-starter-kit|$PROJECT_DIR|g" /etc/systemd/system/containerized-rag.service

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
print_status "Enabling and starting containerized-rag service..."
systemctl enable containerized-rag.service
systemctl start containerized-rag.service

# Check service status
sleep 5
if systemctl is-active --quiet containerized-rag.service; then
    print_status "Service started successfully"
else
    print_error "Service failed to start. Check logs with: journalctl -u containerized-rag.service"
    exit 1
fi

# Setup firewall rules (if ufw is installed)
if command_exists ufw; then
    print_status "Configuring firewall..."
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 22/tcp
    print_warning "Remember to enable UFW if not already enabled: ufw enable"
fi

# Create log directory
mkdir -p /var/log/nginx
touch /var/log/nginx/ilri-archive.access.log
touch /var/log/nginx/ilri-archive.error.log

# Set proper permissions
chown -R www-data:www-data /var/log/nginx

print_status "Deployment completed successfully!"
print_status ""
print_status "The application is now accessible at:"
print_status "- Main site: http://$SERVER_IP"
print_status "- API endpoint: http://$SERVER_IP/api/"
print_status "- Health check: http://$SERVER_IP/health"
print_status ""
print_status "Next steps:"
print_status "1. Run with --setup-ssl to configure self-signed SSL certificate"
print_status "2. Monitor the service with: journalctl -u containerized-rag.service -f"
print_status "3. Check nginx access logs: tail -f /var/log/nginx/ilri-archive.access.log"
print_status ""
print_status "Useful commands:"
print_status "- Service status: systemctl status containerized-rag.service"
print_status "- Restart service: systemctl restart containerized-rag.service"
print_status "- View logs: journalctl -u containerized-rag.service -f"
print_status "- Reload nginx: systemctl reload nginx"