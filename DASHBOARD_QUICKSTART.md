# 🚀 Dashboard Quick Start Guide

Quick guide to launch and test the XTeam Agents Dashboard.

## Prerequisites

```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Have environment variables ready
cp .env.example .env
# Edit .env with your API keys
```

## Launch Dashboard

### Option 1: Full Stack (Recommended)

```bash
# Start all services (MCP server + backends + dashboard)
docker-compose up -d

# Check services are running
docker-compose ps

# Expected output:
# xteam-dashboard      Up
# xteam-mcp-server     Up
# xteam-postgres       Up
# xteam-redis          Up
# xteam-qdrant         Up
# xteam-neo4j          Up
```

### Option 2: Dashboard Only (Dev)

```bash
# Start backends only
docker-compose up -d postgres redis qdrant neo4j

# Run MCP server locally
python -m xteam_agents --http

# In another terminal, run dashboard
cd dashboard
pip install -r requirements.txt
export MCP_SERVER_URL=http://localhost:8000
streamlit run app.py
```

## Access Dashboard

### Development Mode

```bash
# Dashboard runs on port 8501
open http://localhost:8501
```

### Production Mode (with Traefik)

```bash
# Dashboard available via HTTPS
open https://dashboard.example.com

# Other services:
# - MCP Server: https://example.com
# - Traefik Dashboard: https://traefik.example.com
# - Qdrant: https://qdrant.example.com
# - Neo4j: https://neo4j.example.com
```

## Test Dashboard Features

### 1. Test Overview Page

```bash
# Should show:
# - Total Tasks: 0 (or more if you have existing tasks)
# - Active Tasks: 0
# - Completed Tasks: 0
# - Recent Activity table (may be empty)
# - Analytics charts
```

### 2. Submit a Test Task

**Via Sidebar:**
1. Enter description: "Calculate the sum of 1 + 1"
2. Set priority: 3
3. Click "Submit Task"
4. Note the Task ID returned

**Via API:**
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Test task: echo hello world", "priority": 3}'

# Should return: {"task_id": "uuid-here"}
```

### 3. Monitor Live Agents

1. Navigate to **Live Agents** page
2. Select the task you just submitted
3. Watch the cognitive graph update in real-time
4. See Lottie animations for current agent state
5. View live terminal with logs

**Expected flow:**
```
analyze → plan → execute → validate → commit → reflect
```

### 4. Check Adversarial Team

1. Navigate to **Adversarial Team** page
2. Should show:
   - 1 Orchestrator (⚪ idle)
   - 10 Agent-Critic pairs (all ⚪ idle)

**Note**: Adversarial team only activates for complex/critical tasks.

To trigger adversarial team, submit a complex task:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Design and implement a complete authentication system with JWT, refresh tokens, role-based access control, and Redis session management",
    "priority": 5
  }'
```

### 5. Test Quality Metrics

1. Navigate to **Quality Metrics** page
2. Initially may show "No quality metrics available"
3. After completing tasks with adversarial team, should show:
   - 5D radar chart
   - Quality dimensions breakdown
   - Recent evaluations

### 6. Test Chat

1. Navigate to **Chat** page
2. Ask: "What is the system architecture?"
3. Should get RAG-powered response using semantic memory

### 7. Browse Workspace

1. Navigate to **Workspace** page
2. Should show workspace directory contents
3. Click directories to navigate
4. Click "View" on files to read content

### 8. Check Brain Inspector

1. Navigate to **Brain Inspector** page
2. **Semantic Memory**: Search for "task" or "execution"
3. **Episodic Memory**: Select a task to view conversation history

### 9. View Knowledge Graph

1. Navigate to **Knowledge Graph** page
2. Should show count of knowledge nodes from Neo4j
3. Recent knowledge nodes table (may be empty initially)

### 10. Review Audit Log

1. Navigate to **Audit Log** page
2. Should show all system events
3. Filter by task_id, agent, event_type

## Verify API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"xteam-agents","version":"0.1.0"}
```

### List Tasks

```bash
curl http://localhost:8000/api/tasks
# {"tasks": [...]}
```

### Get Agent Status

```bash
curl http://localhost:8000/api/agents/status
# {
#   "cognitive_agents": {...},
#   "adversarial_agents": {...},
#   "total_agents": 16
# }
```

### Search Memory

```bash
curl "http://localhost:8000/api/memory/search?query=test"
# {"results": [...]}
```

### Quality Metrics

```bash
curl http://localhost:8000/api/metrics/quality
# {
#   "quality_data": [...],
#   "average_scores": {...},
#   "total_evaluations": 0
# }
```

## Troubleshooting

### Dashboard won't start

```bash
# Check logs
docker-compose logs dashboard

# Common issues:
# 1. Port 8501 already in use
docker ps | grep 8501
# Kill process or change port

# 2. Missing dependencies
docker-compose build dashboard --no-cache

# 3. Database connection errors
docker-compose logs postgres
ping xteam-postgres  # from dashboard container
```

### MCP Server not responding

```bash
# Check MCP server status
docker-compose logs mcp-server

# Test health endpoint
curl http://mcp-server:8000/health  # from dashboard container
# or
curl http://localhost:8000/health   # from host

# Restart MCP server
docker-compose restart mcp-server
```

### No data in dashboard

```bash
# 1. Check if databases are initialized
docker exec xteam-postgres psql -U postgres -d xteam -c "\dt"

# Should show tables: tasks, audit_log

# 2. Submit test tasks
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Test", "priority": 3}'

# 3. Wait a moment for processing
sleep 5

# 4. Refresh dashboard
```

### Lottie animations not loading

```bash
# Check internet connection (Lottie loads from CDN)
ping lottie.host

# If offline, animations will show placeholder images
# This is expected and doesn't affect functionality
```

## Performance Testing

### Load Test with Multiple Tasks

```bash
# Submit 10 tasks
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/tasks \
    -H "Content-Type: application/json" \
    -d "{\"description\": \"Test task $i\", \"priority\": 3}"
  echo ""
done

# Watch dashboard process them in Live Agents page
```

### Stress Test Auto-Refresh

```bash
# Dashboard auto-refreshes every 5 seconds
# Monitor resource usage:
docker stats xteam-dashboard

# Should stay under:
# - CPU: <10%
# - Memory: <200MB
```

## Integration Test Script

```bash
#!/bin/bash
# test_dashboard.sh

echo "🧪 Testing XTeam Dashboard"

# 1. Check services
echo "✓ Checking services..."
docker-compose ps | grep -q "Up" || exit 1

# 2. Test health endpoint
echo "✓ Testing health endpoint..."
curl -s http://localhost:8000/health | grep -q "ok" || exit 1

# 3. Submit test task
echo "✓ Submitting test task..."
TASK_ID=$(curl -s -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Integration test", "priority": 3}' \
  | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 4. Wait for processing
echo "✓ Waiting for task processing..."
sleep 10

# 5. Get task status
echo "✓ Checking task status..."
curl -s http://localhost:8000/api/tasks/$TASK_ID | jq .

# 6. Check dashboard is accessible
echo "✓ Testing dashboard accessibility..."
curl -s http://localhost:8501 > /dev/null || exit 1

echo "✅ All tests passed!"
```

Run it:
```bash
chmod +x test_dashboard.sh
./test_dashboard.sh
```

## Next Steps

1. **Explore all pages** - Navigate through each dashboard page
2. **Submit real tasks** - Try complex tasks to activate adversarial team
3. **Monitor quality** - Check quality metrics after task completion
4. **Customize** - Edit `dashboard/app.py` to add custom features
5. **Deploy** - Use Traefik for production deployment with SSL

## Production Deployment

### With Traefik (HTTPS)

```bash
# 1. Set domain in .env
echo "DOMAIN=yourdomain.com" >> .env

# 2. Start with Traefik
docker-compose up -d

# 3. Access via HTTPS
open https://dashboard.yourdomain.com
```

### Security

```bash
# Add basic auth to dashboard
# Edit docker-compose.yml, add to dashboard labels:
- "traefik.http.routers.dashboard.middlewares=dash-auth"
- "traefik.http.middlewares.dash-auth.basicauth.users=admin:$$apr1$$..."

# Generate password hash:
htpasswd -nb admin yourpassword
```

## Monitoring

### Dashboard Metrics

```bash
# View dashboard logs
docker-compose logs -f dashboard

# Monitor resource usage
docker stats xteam-dashboard

# Check PostgreSQL connections
docker exec xteam-postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity WHERE datname='xteam';"
```

### System Health

```bash
# Check all services
docker-compose ps

# System health endpoint
curl http://localhost:8000/health

# Memory backends status (via MCP tools)
# Would require MCP client or use dashboard's "System Health" (if we add it)
```

## Useful Commands

```bash
# Restart dashboard only
docker-compose restart dashboard

# Rebuild dashboard after code changes
docker-compose build dashboard && docker-compose up -d dashboard

# View dashboard logs in real-time
docker-compose logs -f dashboard

# Enter dashboard container
docker exec -it xteam-dashboard bash

# Clear dashboard cache
docker exec xteam-dashboard rm -rf ~/.streamlit/cache

# Reset database (⚠️ destroys all data)
docker-compose down -v
docker-compose up -d
```

## Support

- See `dashboard/README.md` for detailed documentation
- Check root `CLAUDE.md` for architecture details
- Report issues: https://github.com/your-org/xteam-agents/issues

---

**Ready to explore!** 🎉 The dashboard is your window into the cognitive operating system.
