# Dashboard & System Expansion Plan

This plan maximizes the dashboard functionality to become a full "Cognitive Operating System" control center, adding file management, system analytics, and enhanced knowledge tools.

## 1. Backend: Expose New Capabilities (FastMCP)
We need to expose internal memory and filesystem operations via HTTP for the Dashboard to consume.
**File:** `src/xteam_agents/server/app.py`

- **Add File Endpoints:**
    - `GET /api/files/list?path={path}`: Wrapper around `list_directory`.
    - `GET /api/files/read?path={path}`: Wrapper around `read_file`.
    - `GET /api/files/download?path={path}`: Return raw file content (Stream).
- **Add Memory Endpoints:**
    - `GET /api/memory/semantic/search?query={q}`: Wrapper around `search_knowledge`.
    - `GET /api/memory/episodic/{task_id}`: Retrieve full conversation history.

## 2. Frontend: Dashboard Expansion (Streamlit)
**File:** `dashboard/app.py`

### 2.1 New Page: "Workspace" (File Explorer)
- **File Browser:** Interactive tree or list view of `./workspace`.
- **Features:**
    - Navigate directories.
    - View file content (code editor view).
    - **Download button** for generated artifacts.

### 2.2 New Page: "Brain Inspector" (Memory Debugger)
- **Semantic Memory Tester:**
    - Input box for a query (e.g., "Docker guidelines").
    - Display returned chunks from Qdrant with relevance scores.
- **Episodic Viewer:**
    - Dropdown to select a Task ID.
    - View raw Redis chat history (User/Assistant messages).

### 2.3 Enhanced "Overview" (System Analytics)
- **Add Charts:**
    - "Task Status Distribution" (Pie Chart).
    - "Daily Task Volume" (Bar Chart).
    - "Average Execution Time" (if data available).

### 2.4 "Chat with System" (Direct Interface)
- A simple Chat Interface (`st.chat_message`) that sends prompts to a generic "User" agent or directly queries the Knowledge Base.
- *Implementation:* Simple POST to `/api/chat` (need to add this endpoint or just use `submit_task` with a specific tag, but a direct `query_memory` tool usage is better for Q&A).

## 3. Implementation Steps
1.  **Server**: Add `FileSystem` and `Memory` REST endpoints to `server/app.py`.
2.  **Dashboard**:
    - Add `show_workspace()` function.
    - Add `show_brain_inspector()` function.
    - Update `show_overview()` with charts (using `plotly` or `altair`).
    - Add `show_chat()` function.
3.  **Refactor**: Move page logic to separate files if `app.py` gets too big (optional, but good for hygiene). *For now, keep in one file for speed unless it exceeds ~500 lines.*

## 4. Verification
- Upload a file via agent (task) -> Verify it appears in "Workspace".
- Create a memory -> Verify it appears in "Brain Inspector".
- Check charts update after new tasks.
