# Dashboard Expansion & Agent Visualization Plan

This plan aims to transform the read-only dashboard into a fully interactive command center for the XTeam Agents system.

## 1. Backend: API Expansion (FastMCP/FastAPI)
To allow the dashboard to control the system, we need to expose REST endpoints on the MCP server.

**File:** `src/xteam_agents/server/app.py`

- **Add Request Models:** `TaskSubmitRequest` (description, priority).
- **Add Endpoints:**
    - `POST /api/tasks`: Accepts JSON, calls `orchestrator.submit_task`.
    - `POST /api/tasks/{task_id}/cancel`: Calls `orchestrator.cancel_task`.

## 2. Frontend: Dashboard Upgrade (Streamlit)
We will significantly enhance `dashboard/app.py`.

### 2.1 Task Management (Control)
- **New Sidebar Section "Actions"**:
    - **"Submit New Task" Form**: Text area for description, priority selector. Sends POST to `/api/tasks`.
- **Enhanced Task List**:
    - Add "Cancel" button next to running tasks (calls `/api/tasks/{id}/cancel`).
    - Add "Delete" button for completed/failed tasks (DB cleanup).

### 2.2 Live Agent Visualization (Observability)
- **New Page "Live Agents"**:
    - **Task Selector**: Dropdown to choose an active task.
    - **Cognitive Graph Visualizer**:
        - Use `graphviz` to render the flow (`Analyze` → `Plan` → `Execute` → `Validate` → `Commit` → `Reflect`).
        - **Dynamic Coloring**: Highlight the current active node in Green based on the latest `audit_log` entry.
        - **Path Tracing**: Highlight visited nodes in Blue.
    - **Real-Time Log Stream**:
        - A scrolling container showing the last 20 audit events for the selected task, auto-refreshing.

## 3. Implementation Steps
1.  **Server Update**: Add REST endpoints to `src/xteam_agents/server/app.py` and restart the server.
2.  **Dashboard Update**: Refactor `dashboard/app.py` to include the new features and Graphviz visualization.
3.  **Verification**: Create a task from the dashboard, watch it move through the graph in the "Live Agents" view, and try canceling it.
