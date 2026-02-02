#!/bin/bash
# Setup script for Traefik deployment

set -e

echo "=== XTeam Agents Traefik Setup ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Create acme.json with correct permissions
echo "Creating acme.json for Let's Encrypt certificates..."
mkdir -p /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data
touch /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json
chmod 600 /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json

echo ""
echo "=== Generate Traefik Dashboard Password ==="
echo ""
echo "To generate a new password for Traefik dashboard, run:"
echo "  docker run --rm httpd:2.4-alpine htpasswd -nb admin YOUR_PASSWORD"
echo ""
echo "Then update the traefik service labels in docker-compose.yml"
echo "Replace the line with traefik.http.middlewares.traefik-auth.basicauth.users"
echo ""

# Check DNS records
echo "=== DNS Records Check ==="
echo ""

# Extract DOMAIN from .env
if [ -f .env ]; then
    DOMAIN=$(grep -E "^DOMAIN=" .env | cut -d'=' -f2)
    if [ -z "$DOMAIN" ]; then
        DOMAIN="example.com"
    fi
else
    DOMAIN="example.com"
fi

echo "Using domain: $DOMAIN"
echo ""
echo "Make sure these DNS A records point to YOUR_SERVER_IP:"
echo "  - $DOMAIN"
echo "  - traefik.$DOMAIN"
echo "  - qdrant.$DOMAIN"
echo "  - neo4j.$DOMAIN"
echo "  - n8n.$DOMAIN"
echo ""
echo "Or use wildcard: *.$DOMAIN"
echo ""
echo "You can verify with:"
echo "  dig $DOMAIN +short"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

echo "=== Starting Services ==="
echo ""
echo "Running: docker-compose up -d"
docker-compose up -d

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Services will be available at:"
echo "  - https://$DOMAIN (Main MCP Server)"
echo "  - https://traefik.$DOMAIN (Traefik Dashboard)"
echo "  - https://qdrant.$DOMAIN (Qdrant Vector DB)"
echo "  - https://neo4j.$DOMAIN (Neo4j Browser)"
echo "  - https://n8n.$DOMAIN (n8n Workflows)"
echo ""
echo "Note: It may take a few minutes for Let's Encrypt certificates to be issued."
echo ""
echo "Check logs with:"
echo "  docker-compose logs -f traefik"
echo ""
