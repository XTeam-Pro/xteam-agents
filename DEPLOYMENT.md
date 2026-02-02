# Deployment Guide

This guide covers deploying XTeam Agents with Traefik reverse proxy and automatic SSL certificates.

## Server Setup

**Server IP**: YOUR_SERVER_IP

**DNS Configuration**: Set the `DOMAIN` variable in `.env` file (default: `example.com`).

The following A records should point to YOUR_SERVER_IP:
- `{DOMAIN}` - Main MCP Server (e.g., `example.com`)
- `traefik.{DOMAIN}` - Traefik Dashboard (e.g., `traefik.example.com`)
- `qdrant.{DOMAIN}` - Qdrant Vector Database UI (e.g., `qdrant.example.com`)
- `neo4j.{DOMAIN}` - Neo4j Browser (e.g., `neo4j.example.com`)
- `n8n.{DOMAIN}` - n8n Workflow Automation (e.g., `n8n.example.com`)

Or use wildcard DNS: `*.{DOMAIN}` pointing to YOUR_SERVER_IP

## Prerequisites

1. Docker and Docker Compose installed
2. Ports 80 and 443 open in firewall
3. DNS records configured and propagated
4. `.env` file configured (copy from `.env.example`)

## Quick Start

```bash
# 1. Clone repository (if not already done)
git clone https://github.com/xteam/xteam-agents.git
cd xteam-agents

# 2. Create and configure .env file
cp .env.example .env
# Edit .env with your API keys and passwords

# 3. Run setup script
sudo ./scripts/setup-traefik.sh
```

## Manual Setup

### 1. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your configuration
nano .env
```

Required variables:
- `DOMAIN` - Base domain (e.g., `example.com`)
- `LETSENCRYPT_EMAIL` - Email for Let's Encrypt notifications
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `NEO4J_PASSWORD`
- `POSTGRES_PASSWORD`
- `N8N_PASSWORD`

### 2. Generate Traefik Dashboard Password

```bash
# Generate password hash (replace YOUR_PASSWORD with actual password)
docker run --rm httpd:2.4-alpine htpasswd -nb admin YOUR_PASSWORD
```

Copy the output and update the `traefik.http.middlewares.traefik-auth.basicauth.users` label in `docker-compose.yml`.

**Important**: In docker-compose.yml, escape dollar signs by doubling them: `$` → `$$`

Example:
```yaml
- "traefik.http.middlewares.traefik-auth.basicauth.users=admin:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/"
```

### 3. Create Certificate Storage

```bash
# Create directory for Let's Encrypt certificates
sudo mkdir -p /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data

# Create acme.json with correct permissions
sudo touch /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json
sudo chmod 600 /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f traefik
```

## Verify Deployment

### Check DNS Resolution

```bash
# Replace {DOMAIN} with your actual domain from .env
dig {DOMAIN} +short
dig traefik.{DOMAIN} +short
dig qdrant.{DOMAIN} +short
dig neo4j.{DOMAIN} +short
dig n8n.{DOMAIN} +short

# Example for default domain (example.com):
dig example.com +short
```

All should return: `YOUR_SERVER_IP`

### Check Certificate Issuance

```bash
# Monitor Traefik logs for certificate generation
docker-compose logs -f traefik | grep -i "certificate"

# Check acme.json for certificates
sudo cat /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json | grep -i "xteam"
```

### Access Services

After certificates are issued (may take 1-2 minutes), services will be available at:

- **MCP Server**: https://{DOMAIN}
- **Traefik Dashboard**: https://traefik.{DOMAIN} (username: `admin`)
- **Qdrant UI**: https://qdrant.{DOMAIN}
- **Neo4j Browser**: https://neo4j.{DOMAIN} (username: `neo4j`)
- **n8n**: https://n8n.{DOMAIN}

Where `{DOMAIN}` is the value from your `.env` file (default: `example.com`)

## Troubleshooting

### Certificates Not Generating

1. Check DNS propagation:
   ```bash
   dig example.com +short
   ```

2. Verify ports 80 and 443 are open:
   ```bash
   sudo netstat -tulpn | grep -E ':(80|443)'
   ```

3. Check Traefik logs:
   ```bash
   docker-compose logs traefik
   ```

4. Verify email in docker-compose.yml:
   ```bash
   grep "acme.email" docker-compose.yml
   ```
   Should show: `cert@example.com`

### 502 Bad Gateway

Service may not be ready yet:
```bash
# Check service health
docker-compose ps

# Check specific service logs
docker-compose logs mcp-server
docker-compose logs qdrant
```

### Traefik Dashboard 401 Unauthorized

Password not configured correctly:
```bash
# Generate new password
docker run --rm httpd:2.4-alpine htpasswd -nb admin YOUR_PASSWORD

# Update docker-compose.yml with output (remember to escape $ as $$)
nano docker-compose.yml

# Restart Traefik
docker-compose restart traefik
```

## Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f traefik
docker-compose logs -f mcp-server
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart traefik
docker-compose restart mcp-server
```

### Update Deployment

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Clean up old images
docker image prune -f
```

### Backup

#### Backup Volumes

```bash
# Create backup directory
mkdir -p backups

# Backup all volumes
docker run --rm \
  -v xteam-agents_traefik-certificates:/source/traefik \
  -v xteam-agents_redis-data:/source/redis \
  -v xteam-agents_qdrant-data:/source/qdrant \
  -v xteam-agents_neo4j-data:/source/neo4j \
  -v xteam-agents_postgres-data:/source/postgres \
  -v xteam-agents_n8n-data:/source/n8n \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/xteam-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .
```

#### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore (replace BACKUP_FILE with actual file)
docker run --rm \
  -v xteam-agents_traefik-certificates:/target/traefik \
  -v xteam-agents_redis-data:/target/redis \
  -v xteam-agents_qdrant-data:/target/qdrant \
  -v xteam-agents_neo4j-data:/target/neo4j \
  -v xteam-agents_postgres-data:/target/postgres \
  -v xteam-agents_n8n-data:/target/n8n \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/BACKUP_FILE -C /target

# Start services
docker-compose up -d
```

## Security Considerations

1. **Change default passwords**: Update all passwords in `.env` file
2. **Restrict Traefik dashboard**: Only allow access from trusted IPs if needed
3. **Regular updates**: Keep Docker images updated
4. **Firewall**: Only expose ports 80, 443, and 22 (SSH)
5. **Monitoring**: Set up monitoring for service health and certificate expiry

## SSL Certificate Renewal

Let's Encrypt certificates are valid for 90 days and are automatically renewed by Traefik when they have 30 days or less remaining. No manual intervention is required.

To force certificate renewal:
```bash
# Remove acme.json
sudo rm /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json

# Restart Traefik
docker-compose restart traefik
```

## Support

For issues related to:
- **Deployment**: Check this guide and Traefik logs
- **Application**: See main README.md
- **Development**: See CLAUDE.md

Logs location:
- Traefik: `docker-compose logs traefik`
- Application: `docker-compose logs mcp-server`
- Databases: `docker-compose logs redis qdrant neo4j postgres`
