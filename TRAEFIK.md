# Traefik Configuration

## Service URLs

After deployment with Traefik, services are accessible at (replace `{DOMAIN}` with your domain from `.env`):

| Service | URL Pattern | Example (default) |
|---------|-------------|-------------------|
| MCP Server | https://{DOMAIN} | https://example.com |
| Traefik Dashboard | https://traefik.{DOMAIN} | https://traefik.example.com |
| Qdrant | https://qdrant.{DOMAIN} | https://qdrant.example.com |
| Neo4j | https://neo4j.{DOMAIN} | https://neo4j.example.com |
| n8n | https://n8n.{DOMAIN} | https://n8n.example.com |

## Configuration Details

### Server Information
- **IP Address**: YOUR_SERVER_IP
- **Domain Configuration**: Set via `DOMAIN` variable in `.env` file
- **Let's Encrypt Email**: Set via `LETSENCRYPT_EMAIL` variable in `.env` file
- **Certificate Resolver**: TLS Challenge (port 443)

### DNS Configuration Required

All domains must have A records pointing to YOUR_SERVER_IP.

Replace `{DOMAIN}` with your actual domain from `.env` (default: `example.com`):

```
{DOMAIN}                A    YOUR_SERVER_IP
traefik.{DOMAIN}        A    YOUR_SERVER_IP
qdrant.{DOMAIN}         A    YOUR_SERVER_IP
neo4j.{DOMAIN}          A    YOUR_SERVER_IP
n8n.{DOMAIN}            A    YOUR_SERVER_IP
```

**Wildcard alternative (recommended):**
```
*.{DOMAIN}              A    YOUR_SERVER_IP
{DOMAIN}                A    YOUR_SERVER_IP
```

**Example for default domain (example.com):**
```
example.com        A    YOUR_SERVER_IP
*.example.com      A    YOUR_SERVER_IP
```

### Features Enabled

- ✅ Automatic HTTPS with Let's Encrypt
- ✅ HTTP to HTTPS redirect
- ✅ Docker provider with automatic service discovery
- ✅ Dashboard with basic authentication
- ✅ Certificate auto-renewal (90 days validity, renewed at 30 days)

## Quick Commands

### Check Certificate Status

```bash
# View acme.json content
sudo cat /var/lib/docker/volumes/xteam-agents_traefik-certificates/_data/acme.json | jq

# Check Traefik logs for certificate events
docker-compose logs traefik | grep -i certificate
```

### Generate New Dashboard Password

```bash
# Generate password (replace YOUR_PASSWORD)
docker run --rm httpd:2.4-alpine htpasswd -nb admin YOUR_PASSWORD

# Output will be like:
# admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/

# Update in docker-compose.yml (escape $ as $$):
# traefik.http.middlewares.traefik-auth.basicauth.users=admin:$$apr1$$H6uskkkW$$IgXLP6ewTrSuBkTrqE8wj/
```

### Test Service Availability

```bash
# Test main MCP server
curl -k https://example.com/health

# Test Qdrant
curl -k https://qdrant.example.com/

# Test Neo4j
curl -k https://neo4j.example.com/
```

### View Traefik Dashboard

1. Navigate to https://traefik.example.com
2. Login with credentials:
   - Username: `admin`
   - Password: (set in docker-compose.yml)
3. View:
   - HTTP routers and their rules
   - Services and health status
   - Middlewares (auth, redirects)
   - Certificates status

## Traefik Labels Explained

### MCP Server Example

```yaml
labels:
  - "traefik.enable=true"                                           # Enable Traefik for this service
  - "traefik.http.routers.mcp-server.rule=Host(`example.com`)" # Route by hostname
  - "traefik.http.routers.mcp-server.entrypoints=websecure"        # Use HTTPS entrypoint (443)
  - "traefik.http.routers.mcp-server.tls.certresolver=letsencrypt" # Use Let's Encrypt
  - "traefik.http.services.mcp-server.loadbalancer.server.port=8000" # Backend port
```

### With Basic Auth (Traefik Dashboard)

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.traefik.rule=Host(`traefik.example.com`)"
  - "traefik.http.routers.traefik.entrypoints=websecure"
  - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
  - "traefik.http.routers.traefik.service=api@internal"            # Built-in dashboard service
  - "traefik.http.routers.traefik.middlewares=traefik-auth"       # Apply auth middleware
  - "traefik.http.middlewares.traefik-auth.basicauth.users=..."   # User credentials
```

## Advanced Configuration

### Add New Service

To expose a new service through Traefik:

1. Add service to docker-compose.yml
2. Add to xteam-network
3. Use `expose` instead of `ports` for internal port
4. Add Traefik labels:

```yaml
my-service:
  image: my-image:latest
  expose:
    - "3000"
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.my-service.rule=Host(`myservice.example.com`)"
    - "traefik.http.routers.my-service.entrypoints=websecure"
    - "traefik.http.routers.my-service.tls.certresolver=letsencrypt"
    - "traefik.http.services.my-service.loadbalancer.server.port=3000"
  networks:
    - xteam-network
```

5. Add DNS A record for `myservice.example.com`

### IP Whitelist Middleware

To restrict access to specific IPs:

```yaml
labels:
  - "traefik.http.middlewares.ip-whitelist.ipwhitelist.sourcerange=1.2.3.4/32,5.6.7.8/32"
  - "traefik.http.routers.my-service.middlewares=ip-whitelist"
```

### Rate Limiting

To add rate limiting:

```yaml
labels:
  - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
  - "traefik.http.middlewares.rate-limit.ratelimit.burst=50"
  - "traefik.http.routers.my-service.middlewares=rate-limit"
```

## Troubleshooting

### Certificate Issues

**Problem**: Certificate not generating

**Solutions**:
1. Verify DNS points to correct IP: `dig example.com +short`
2. Check port 443 is accessible: `telnet YOUR_SERVER_IP 443`
3. View Traefik logs: `docker-compose logs traefik | grep -i acme`
4. Verify email in config: `grep acme.email docker-compose.yml`

**Problem**: Certificate expired

**Solutions**:
1. Check auto-renewal is working: `docker-compose logs traefik | grep renew`
2. Force renewal by removing acme.json and restarting
3. Verify Traefik container has been running continuously

### Service Not Accessible

**Problem**: 502 Bad Gateway

**Solutions**:
1. Check service health: `docker-compose ps`
2. Verify service logs: `docker-compose logs [service-name]`
3. Check network connectivity: `docker network inspect xteam-agents_xteam-network`
4. Verify port in label matches service port

**Problem**: 404 Not Found

**Solutions**:
1. Check router configuration in Traefik dashboard
2. Verify DNS resolution: `nslookup myservice.example.com`
3. Check Traefik can discover service: `docker-compose logs traefik | grep [service-name]`

### Dashboard Not Accessible

**Problem**: 401 Unauthorized

**Solutions**:
1. Verify password is correct
2. Check password is properly escaped in docker-compose.yml ($ → $$)
3. Regenerate password: `docker run --rm httpd:2.4-alpine htpasswd -nb admin newpassword`
4. Update docker-compose.yml and restart: `docker-compose restart traefik`

## Monitoring

### Health Check Endpoints

```bash
# Traefik health (JSON)
curl https://traefik.example.com/ping

# MCP Server health
curl https://example.com/health

# Qdrant health
curl https://qdrant.example.com/

# Neo4j health
curl https://neo4j.example.com/
```

### Certificate Expiry

Certificates are automatically renewed by Traefik 30 days before expiry. To check:

```bash
# View certificate details
echo | openssl s_client -servername example.com -connect example.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Log Monitoring

```bash
# Follow all Traefik logs
docker-compose logs -f traefik

# Filter for errors
docker-compose logs traefik | grep -i error

# Filter for certificate events
docker-compose logs traefik | grep -i "obtain certificate\|renew certificate"

# Filter for specific domain
docker-compose logs traefik | grep example.com
```

## Security Best Practices

1. **Change Default Passwords**: Update Traefik dashboard password immediately
2. **Restrict Dashboard Access**: Consider IP whitelist for Traefik dashboard
3. **Keep Updated**: Regularly update Traefik image version
4. **Monitor Logs**: Set up log aggregation and alerts
5. **Backup acme.json**: Regular backups of certificate storage
6. **Use Strong Passwords**: For all services (Neo4j, PostgreSQL, n8n)
7. **Firewall Rules**: Only allow ports 22, 80, 443 from internet

## References

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Labels Reference](https://doc.traefik.io/traefik/reference/dynamic-configuration/docker/)
