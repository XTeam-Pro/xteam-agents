# 🎛️ XTeam Agents Dashboard

Interactive web dashboard for monitoring and controlling the XTeam Agents Cognitive Operating System.

## Features

### 📊 Overview
- System-wide statistics (total/active/completed tasks)
- Recent activity timeline
- Task status distribution
- Activity volume charts (24h)

### 🤖 Live Agents
- Real-time cognitive graph visualization
- Current agent state with Lottie animations
- Live terminal with audit log streaming
- Task execution progress tracking

### 🤺 Adversarial Team
- **NEW!** Monitor all 21 AI agents:
  - 1 Supreme Orchestrator
  - 10 Agent-Critic Pairs
- View agent-critic debate cycles
- Track agent strategies (Normal/Perfectionist/Adversarial)
- Real-time agent status indicators

### 📈 Quality Metrics
- **NEW!** 5D Quality Scoring visualization:
  - Correctness
  - Completeness
  - Efficiency
  - Maintainability
  - Security
- Radar charts for quality profiles
- Historical quality trends
- Approval threshold indicators
- Per-agent quality comparison

### 💬 Chat
- Interactive chat with the system
- RAG-powered responses using semantic memory
- Context-aware answers

### 📋 Tasks
- List all tasks with status
- Task detail view with audit log
- Cancel/manage tasks
- Submit new tasks via sidebar form

### 📁 Workspace
- Browse agent workspace files
- Navigate directory tree
- View file contents inline
- Code highlighting

### 🧠 Brain Inspector
- **Semantic Memory**: Search validated knowledge
- **Episodic Memory**: View conversation history
- Debug memory operations

### 🕸️ Knowledge Graph
- Visualize procedural memory from Neo4j
- Browse knowledge nodes
- View relationships and metadata

### 📜 Audit Log
- Complete system audit trail
- All events, agents, and operations
- Exportable data tables

## Architecture

### Technology Stack
- **Frontend**: Streamlit (Python)
- **Visualization**: Plotly, Graphviz, Lottie animations
- **Data**: Pandas, psycopg2 (PostgreSQL), neo4j
- **API**: REST API endpoints from MCP server

### Data Flow

```
Dashboard → REST API → MCP Server → Orchestrator
                                        ↓
                        ┌───────────────┴───────────────┐
                        ↓                               ↓
                Cognitive Graph                 Memory Manager
                (5 agents)                      (4 backends)
                        ↓                               ↓
                Adversarial Team ───────────────→ Audit Log
                (21 agents)                      (PostgreSQL)
```

### REST API Endpoints

The dashboard communicates with the MCP server via these endpoints:

**Tasks:**
- `GET /api/tasks` - List all tasks
- `POST /api/tasks` - Submit new task
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks/{id}/cancel` - Cancel task

**Agents:**
- `GET /api/agents/status` - Get all agent statuses (cognitive + adversarial)

**Memory:**
- `GET /api/memory/search` - Search semantic memory

**Metrics:**
- `GET /api/metrics/quality` - Get quality scores and 5D metrics

**Files:**
- `GET /api/files/list` - List workspace files
- `GET /api/files/read` - Read file content

**Chat:**
- `POST /api/chat` - Chat with system

## Installation

### Docker (Recommended)

Dashboard is included in the main docker-compose.yml:

```bash
# Start all services including dashboard
docker-compose up -d

# Access dashboard at:
# - Development: http://localhost:8501
# - Production: https://dashboard.example.com (via Traefik)
```

### Standalone

```bash
cd dashboard

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PASSWORD=xteam_password
export NEO4J_URL=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=xteam_password
export MCP_SERVER_URL=http://localhost:8000

# Run dashboard
streamlit run app.py
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL hostname | `localhost` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `xteam_password` |
| `NEO4J_URL` | Neo4j connection URL | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `xteam_password` |
| `MCP_SERVER_URL` | MCP server base URL | `http://localhost:8000` |

### Customization

**Auto-refresh interval** (app.py line 80):
```python
st_autorefresh(interval=5000, key="data_refresh")  # 5 seconds
```

**Color theme** (app.py lines 22-76):
Custom CSS with cyberpunk/glassmorphism styling

**Lottie animations** (app.py lines 87-95):
Configure animation URLs for different agent states

## Usage

### Monitoring Active Tasks

1. Navigate to **Live Agents** page
2. Select a task from the dropdown
3. Watch real-time execution:
   - Cognitive graph with current node highlighted
   - Lottie animation showing agent activity
   - Live terminal with streaming logs

### Tracking Adversarial Team

1. Navigate to **Adversarial Team** page
2. View all 21 agents and their status
3. Check which agent-critic pairs are active
4. Review recent debates and quality feedback

### Analyzing Quality

1. Navigate to **Quality Metrics** page
2. View 5D radar chart for quality profile
3. Compare scores across dimensions
4. Check if scores meet approval threshold (7.0)
5. Review historical evaluations

### Submitting Tasks

**Via Sidebar:**
1. Fill in task description
2. Set priority (1-5)
3. Click "Submit Task"
4. Task ID will be displayed

**Via Chat:**
1. Navigate to **Chat** page
2. Type your question or request
3. System will respond using RAG + memory

### Browsing Workspace

1. Navigate to **Workspace** page
2. Click directories to navigate
3. Click "View" on files to see contents
4. Use "⬆️ Up" button to go back

## Development

### Adding New Pages

1. Create page function in `app.py`:
```python
def show_my_page():
    st.title("My Page")
    # Your code here
```

2. Add to navigation:
```python
page = st.sidebar.radio("Navigation", [
    ...,
    "My Page"
])
```

3. Add routing:
```python
elif page == "My Page":
    show_my_page()
```

### Adding New Metrics

1. Create API endpoint in MCP server
2. Call endpoint from dashboard
3. Visualize using Plotly/Streamlit components

## Troubleshooting

### Connection Errors

**Problem**: "Connection failed: [Errno 111] Connection refused"

**Solution**:
- Ensure MCP server is running: `docker ps | grep mcp-server`
- Check MCP_SERVER_URL environment variable
- Verify network connectivity: `docker exec xteam-dashboard ping mcp-server`

### Database Errors

**Problem**: "psycopg2.OperationalError: could not connect"

**Solution**:
- Ensure PostgreSQL is running: `docker ps | grep postgres`
- Check POSTGRES_HOST and POSTGRES_PASSWORD
- Verify database exists: `docker exec xteam-postgres psql -U postgres -c "\l"`

### Missing Data

**Problem**: Dashboard shows "No data"

**Solution**:
- Submit test tasks to generate data
- Check audit log for events
- Ensure services are initialized: `docker-compose logs`

### Lottie Animations Not Loading

**Problem**: Animations show placeholder images

**Solution**:
- Check internet connectivity (Lottie loads from CDN)
- Host Lottie files locally if needed
- Update LOTTIE_URLS in app.py

## Performance

### Optimization Tips

1. **Reduce auto-refresh interval** for less frequent updates
2. **Limit data queries** - adjust LIMIT in SQL queries
3. **Cache expensive operations** - use `@st.cache_data` decorator
4. **Paginate large datasets** - add pagination to tables

### Resource Usage

- **Memory**: ~100-200 MB per dashboard instance
- **CPU**: Low (<5%) during idle, spikes during data loading
- **Network**: Minimal, only API calls on page load/refresh

## Security

### Production Deployment

1. **Use HTTPS**: Traefik handles SSL certificates automatically
2. **Add authentication**: Configure Streamlit auth or use Traefik middleware
3. **Restrict access**: Use firewall rules or VPN
4. **Secure credentials**: Use environment variables, never hardcode

### Authentication

**Option 1: Basic Auth via Traefik**

Add to dashboard labels in docker-compose.yml:
```yaml
- "traefik.http.routers.dashboard.middlewares=dashboard-auth"
- "traefik.http.middlewares.dashboard-auth.basicauth.users=user:$$apr1$$..."
```

**Option 2: Streamlit Authentication**

Install streamlit-authenticator:
```bash
pip install streamlit-authenticator
```

Add to app.py:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')

if not authentication_status:
    st.stop()
```

## Roadmap

- [ ] Real-time WebSocket updates (eliminate polling)
- [ ] Task templates and presets
- [ ] Agent performance analytics
- [ ] Custom metric dashboards
- [ ] Export reports (PDF, CSV)
- [ ] Mobile-responsive design
- [ ] Dark/light theme toggle
- [ ] Multi-user collaboration
- [ ] Integration with CI/CD pipelines

## Contributing

Contributions welcome! Areas for improvement:

- Additional visualizations
- Performance optimizations
- New dashboard pages
- Better error handling
- Unit tests for dashboard

## License

Same as parent project (see root LICENSE file)

## Support

- **Issues**: https://github.com/your-org/xteam-agents/issues
- **Documentation**: See root README.md and CLAUDE.md
- **Community**: [Discord/Slack link]

---

**Built with** ❤️ **using Streamlit and the XTeam Agents Cognitive OS**
