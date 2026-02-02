# Quick Start Guide

## For Production Deployment (YOUR_SERVER_IP)

### 1. Initial Setup

```bash
cd /root/xteam-agents
cp .env.example .env
nano .env  # Add your API keys and passwords
sudo ./scripts/setup-traefik.sh
```

### 2. Verify DNS

```bash
# Replace {DOMAIN} with your domain from .env file
dig {DOMAIN} +short                  # Should return: YOUR_SERVER_IP
dig traefik.{DOMAIN} +short          # Should return: YOUR_SERVER_IP

# For default domain (example.com):
dig example.com +short          # Should return: YOUR_SERVER_IP
```

### 3. Access Services

Replace `{DOMAIN}` with your domain from `.env` file (default: `example.com`):

- **MCP Server**: https://{DOMAIN}
- **Traefik Dashboard**: https://traefik.{DOMAIN} (user: admin)
- **Qdrant**: https://qdrant.{DOMAIN}
- **Neo4j**: https://neo4j.{DOMAIN} (user: neo4j)
- **n8n**: https://n8n.{DOMAIN}

## For Local Development

### 1. Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
nano .env  # Add API keys

# Start services
docker-compose up -d
```

### 2. Access Services

- **MCP Server**: http://localhost:8000
- **Redis**: localhost:6379
- **Qdrant**: http://localhost:6333
- **Neo4j**: http://localhost:7474 (user: neo4j)
- **PostgreSQL**: localhost:5432
- **n8n**: http://localhost:5678

### 3. Run Tests

```bash
pytest                           # All tests
pytest tests/unit/              # Unit tests only
pytest --cov=xteam_agents       # With coverage
```

## Common Operations

### Deploy/Update

```bash
cd /root/xteam-agents
git pull
docker-compose up -d --build
docker image prune -f
```

### View Logs

```bash
docker-compose logs -f                    # All services
docker-compose logs -f traefik            # Traefik only
docker-compose logs -f mcp-server         # MCP server only
docker-compose logs --tail=100 traefik    # Last 100 lines
```

### Restart Services

```bash
docker-compose restart                    # All services
docker-compose restart traefik            # Traefik only
docker-compose restart mcp-server         # MCP server only
```

### Check Status

```bash
docker-compose ps                         # Service status
docker-compose logs traefik | grep -i certificate  # Certificate status

# Health check (replace {DOMAIN} with your domain)
curl -k https://{DOMAIN}/health          # Health check
```

### Change Traefik Password

```bash
# Generate new password
docker run --rm httpd:2.4-alpine htpasswd -nb admin YOUR_NEW_PASSWORD

# Update docker-compose.yml with output (escape $ as $$)
nano docker-compose.yml

# Restart
docker-compose restart traefik
```

### Backup Data

```bash
# Create backup
docker run --rm \
  -v xteam-agents_traefik-certificates:/source/traefik \
  -v xteam-agents_redis-data:/source/redis \
  -v xteam-agents_qdrant-data:/source/qdrant \
  -v xteam-agents_neo4j-data:/source/neo4j \
  -v xteam-agents_postgres-data:/source/postgres \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /source .
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h

# Restart Docker
sudo systemctl restart docker
docker-compose up -d
```

### SSL Certificate Issues

```bash
# Check DNS (replace {DOMAIN} with your domain from .env)
dig {DOMAIN} +short

# Check ports
sudo netstat -tulpn | grep -E ':(80|443)'

# View certificate logs
docker-compose logs traefik | grep -i acme

# Force renewal (remove certificates)
sudo rm /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json
docker-compose restart traefik
```

### 502 Bad Gateway

```bash
# Check service health
docker-compose ps

# Check service logs
docker-compose logs mcp-server

# Restart service
docker-compose restart mcp-server
```

### Database Connection Issues

```bash
# Check database containers
docker-compose ps postgres neo4j redis qdrant

# Restart databases
docker-compose restart postgres neo4j redis qdrant

# Check database logs
docker-compose logs postgres
docker-compose logs neo4j
```

## Environment Variables

Key variables in `.env`:

```bash
# Domain Configuration
DOMAIN=example.com                       # Base domain for all services
LETSENCRYPT_EMAIL=cert@example.com              # Email for Let's Encrypt

# LLM Configuration
LLM_PROVIDER=openai                           # or anthropic
OPENAI_API_KEY=sk-...                         # Required if using OpenAI
ANTHROPIC_API_KEY=sk-ant-...                  # Required if using Anthropic
LLM_MODEL=gpt-4o                              # or claude-3-5-sonnet-20241022

# Database Passwords
NEO4J_PASSWORD=your_secure_password
POSTGRES_PASSWORD=your_secure_password
N8N_PASSWORD=your_secure_password

# Optional
LOG_LEVEL=INFO                                # DEBUG for development
TASK_TIMEOUT_SECONDS=300
MAX_REPLAN_ITERATIONS=3
```

## File Structure Reference

```
/root/xteam-agents/
├── docker-compose.yml        # Service definitions with Traefik
├── .env                      # Environment configuration (create from .env.example)
├── DEPLOYMENT.md             # Full deployment guide
├── TRAEFIK.md               # Traefik configuration details
├── CLAUDE.md                # Guide for Claude Code
├── QUICKSTART.md            # This file
├── scripts/
│   └── setup-traefik.sh     # Automated setup script
└── src/xteam_agents/        # Application source code
```

## Support Resources

- **Deployment Issues**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Traefik Issues**: See [TRAEFIK.md](TRAEFIK.md)
- **Development**: See [CLAUDE.md](CLAUDE.md)
- **Architecture**: See [README.md](README.md)

## Quick Health Check

```bash
# One-liner to check all services (replace {DOMAIN} with your domain)
DOMAIN="example.com"  # Set your domain here
curl -sk https://${DOMAIN}/health && \
curl -sk https://qdrant.${DOMAIN}/ && \
curl -sk https://neo4j.${DOMAIN}/ && \
echo "All services healthy"
```

## Emergency Procedures

### Complete System Reset

```bash
# WARNING: This will delete ALL data!
docker-compose down -v
docker-compose up -d
```

### Service-Specific Reset

```bash
# Reset single service data
docker-compose down
docker volume rm xteam-agents_redis-data     # Redis only
docker volume rm xteam-agents_qdrant-data    # Qdrant only
docker-compose up -d
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore backup (replace BACKUP_FILE)
docker run --rm \
  -v xteam-agents_traefik-certificates:/target/traefik \
  -v xteam-agents_redis-data:/target/redis \
  -v xteam-agents_qdrant-data:/target/qdrant \
  -v xteam-agents_neo4j-data:/target/neo4j \
  -v xteam-agents_postgres-data:/target/postgres \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/BACKUP_FILE -C /target

# Restart
docker-compose up -d
```
