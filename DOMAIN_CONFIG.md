# Domain Configuration Guide

## Overview

The project uses a single `DOMAIN` variable in `.env` file, with automatic subdomain generation for each service in `docker-compose.yml`.

## Configuration Structure

### In `.env` file:

```bash
# Base domain for all services
DOMAIN=example.com

# Let's Encrypt email for SSL certificates
LETSENCRYPT_EMAIL=cert@example.com
```

### In `docker-compose.yml`:

Each service automatically generates its domain using the `DOMAIN` variable:

| Service | Domain Pattern | Example | Environment Variable |
|---------|---------------|---------|---------------------|
| **MCP Server** | `${DOMAIN}` | `example.com` | `MCP_SERVER_DOMAIN` |
| **Traefik Dashboard** | `traefik.${DOMAIN}` | `traefik.example.com` | `TRAEFIK_DOMAIN` |
| **Qdrant** | `qdrant.${DOMAIN}` | `qdrant.example.com` | `QDRANT_DOMAIN` |
| **Neo4j** | `neo4j.${DOMAIN}` | `neo4j.example.com` | `NEO4J_DOMAIN` |
| **n8n** | `n8n.${DOMAIN}` | `n8n.example.com` | `N8N_DOMAIN` |

## How It Works

### 1. Domain Variable in Labels

Each service uses the `DOMAIN` variable in Traefik labels:

```yaml
labels:
  - "traefik.http.routers.SERVICE.rule=Host(`SUBDOMAIN.${DOMAIN:-example.com}`)"
```

The `:-example.com` part provides a default value if `DOMAIN` is not set.

### 2. Environment Variables for Services

Each service also gets its full domain as an environment variable:

```yaml
environment:
  - SERVICE_DOMAIN=subdomain.${DOMAIN:-example.com}
```

This allows the service itself to know its public domain (useful for webhooks, redirects, etc.).

## Examples

### Example 1: Default Domain (example.com)

`.env` file:
```bash
DOMAIN=example.com
LETSENCRYPT_EMAIL=cert@example.com
```

Services will be available at:
- https://example.com (MCP Server)
- https://traefik.example.com (Traefik)
- https://qdrant.example.com (Qdrant)
- https://neo4j.example.com (Neo4j)
- https://n8n.example.com (n8n)

### Example 2: Custom Domain (mycompany.com)

`.env` file:
```bash
DOMAIN=mycompany.com
LETSENCRYPT_EMAIL=ssl@mycompany.com
```

Services will be available at:
- https://mycompany.com (MCP Server)
- https://traefik.mycompany.com (Traefik)
- https://qdrant.mycompany.com (Qdrant)
- https://neo4j.mycompany.com (Neo4j)
- https://n8n.mycompany.com (n8n)

### Example 3: Subdomain Base (api.company.com)

`.env` file:
```bash
DOMAIN=api.company.com
LETSENCRYPT_EMAIL=devops@company.com
```

Services will be available at:
- https://api.company.com (MCP Server)
- https://traefik.api.company.com (Traefik)
- https://qdrant.api.company.com (Qdrant)
- https://neo4j.api.company.com (Neo4j)
- https://n8n.api.company.com (n8n)

## DNS Configuration

You need to create DNS A records for all domains pointing to your server IP (YOUR_SERVER_IP):

### Option 1: Individual Records

```
DOMAIN                  A    YOUR_SERVER_IP
traefik.DOMAIN          A    YOUR_SERVER_IP
qdrant.DOMAIN           A    YOUR_SERVER_IP
neo4j.DOMAIN            A    YOUR_SERVER_IP
n8n.DOMAIN              A    YOUR_SERVER_IP
```

### Option 2: Wildcard (Recommended)

```
DOMAIN                  A    YOUR_SERVER_IP
*.DOMAIN                A    YOUR_SERVER_IP
```

This covers all subdomains automatically.

## Changing Domain After Deployment

If you need to change the domain after initial deployment:

1. Update `DOMAIN` in `.env` file:
   ```bash
   nano .env
   # Change DOMAIN=old.domain to DOMAIN=new.domain
   ```

2. Update DNS records to point to your server IP

3. Remove old certificates:
   ```bash
   sudo rm /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json
   ```

4. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

5. Wait 1-2 minutes for new certificates to be issued

## Technical Implementation

### Traefik Label Example (MCP Server)

```yaml
mcp-server:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.mcp-server.rule=Host(`${DOMAIN:-example.com}`)"
    - "traefik.http.routers.mcp-server.entrypoints=websecure"
    - "traefik.http.routers.mcp-server.tls.certresolver=letsencrypt"
    - "traefik.http.services.mcp-server.loadbalancer.server.port=8000"
  environment:
    - MCP_SERVER_DOMAIN=${DOMAIN:-example.com}
```

### How Docker Compose Resolves Variables

1. Docker Compose reads `.env` file
2. Variables are substituted in `docker-compose.yml` at runtime
3. `${DOMAIN}` is replaced with value from `.env`
4. `${DOMAIN:-example.com}` uses default if `DOMAIN` not set

### Let's Encrypt Email Configuration

The email for Let's Encrypt is configured in Traefik command:

```yaml
traefik:
  command:
    - "--certificatesresolvers.letsencrypt.acme.email=${LETSENCRYPT_EMAIL:-cert@example.com}"
```

## Verification

### Check Current Domain Configuration

```bash
# Show domain from .env
grep "^DOMAIN=" .env

# Show resolved domain in running container
docker exec xteam-traefik env | grep DOMAIN

# Show domain in service environment
docker exec xteam-mcp-server env | grep DOMAIN
```

### Test Domain Resolution

```bash
# Get domain from .env
DOMAIN=$(grep "^DOMAIN=" .env | cut -d'=' -f2)

# Test DNS resolution
dig $DOMAIN +short
dig traefik.$DOMAIN +short
dig qdrant.$DOMAIN +short

# Test HTTPS access
curl -I https://$DOMAIN/health
```

## Troubleshooting

### Problem: Services not accessible after changing domain

**Solution:**
1. Verify DNS records: `dig NEW_DOMAIN +short`
2. Check if records propagated: `nslookup NEW_DOMAIN 8.8.8.8`
3. Wait for DNS propagation (can take up to 24 hours, usually 5-10 minutes)
4. Force certificate renewal (see "Changing Domain" section)

### Problem: Certificate not issued for new domain

**Solution:**
1. Check Traefik logs: `docker-compose logs traefik | grep -i acme`
2. Verify DNS points to correct IP
3. Ensure ports 80 and 443 are open
4. Check Let's Encrypt rate limits (50 certs per domain per week)

### Problem: Mixed domains (old and new)

**Solution:**
1. Fully restart all services: `docker-compose down && docker-compose up -d`
2. Clear browser cache
3. Remove old certificates: `sudo rm /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json`

## Best Practices

1. **Use wildcard DNS** - Easier to manage, covers all subdomains
2. **Set domain before first deployment** - Avoids certificate reissuance
3. **Use meaningful domain** - Makes services easy to remember
4. **Keep LETSENCRYPT_EMAIL updated** - Important for certificate expiry notifications
5. **Document custom domains** - If using non-standard domain, document it for team

## Security Notes

1. **Domain ownership** - Ensure you control the domain before configuring
2. **Certificate transparency** - All Let's Encrypt certs are publicly logged
3. **Subdomain exposure** - Wildcard DNS exposes all subdomains structure
4. **Email privacy** - Let's Encrypt email is included in cert metadata
5. **Rate limits** - Let's Encrypt has rate limits, avoid frequent changes

## Integration with Services

### n8n Webhooks

n8n automatically uses its domain for webhooks:

```yaml
environment:
  - WEBHOOK_URL=https://n8n.${DOMAIN:-example.com}/
```

### Neo4j Browser

Neo4j browser will be accessible at its configured domain and automatically connect to the correct bolt:// URL.

### Application Callbacks

If your application needs to know its public URL, use the environment variable:

```python
import os
mcp_domain = os.getenv('MCP_SERVER_DOMAIN', 'example.com')
public_url = f'https://{mcp_domain}'
```

## Summary

The domain configuration system provides:

- ✅ Single source of truth (`DOMAIN` in `.env`)
- ✅ Automatic subdomain generation for all services
- ✅ Easy to change domain without modifying docker-compose.yml
- ✅ Default values for local development
- ✅ Service-specific environment variables for application use
- ✅ Automatic SSL certificates for all configured domains
