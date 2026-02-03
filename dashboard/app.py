import streamlit as st
from streamlit_autorefresh import st_autorefresh
import psycopg2
import pandas as pd
import os
import time
import requests
import json
from datetime import datetime
from neo4j import GraphDatabase
import graphviz
from streamlit_lottie import st_lottie

# Configuration
st.set_page_config(
    page_title="XTeam Agents Dashboard",
    page_icon="🤖",
    layout="wide",
)

# --- Custom CSS (Cyberpunk/Glassmorphism) ---
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Cards / Containers */
    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #2ea043;
        box-shadow: 0 0 10px rgba(46, 160, 67, 0.5);
    }
    
    /* Logs / Terminal */
    .stCode {
        background-color: #0d1117 !important;
        border: 1px solid #30363d;
        color: #c9d1d9 !important;
    }
    
    /* Progress/Status Colors */
    .status-active { color: #3fb950; text-shadow: 0 0 5px #3fb950; }
    .status-error { color: #f85149; text-shadow: 0 0 5px #f85149; }
    .status-idle { color: #8b949e; }
    
</style>
""", unsafe_allow_html=True)

# Auto refresh every 5 seconds
st_autorefresh(interval=5000, key="data_refresh")

# --- Constants ---
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://xteam-mcp-server:8000")

# --- Lottie Animations ---
# Fallback URLs if LottieFiles is down, using public reliable JSONs or Placeholders
LOTTIE_URLS = {
    "analyze": "https://lottie.host/0a068406-880c-4806-b33c-3647321e0649/m8K8yR2u2M.json", # Robot Thinking
    "plan": "https://lottie.host/5a70376d-888e-473d-8205-062e2402120e/j3mF3Z0K2n.json",    # Blueprint/Writing
    "execute": "https://lottie.host/80860888-0056-4299-9238-164478144078/g7k5G9u72m.json", # Robot Typing
    "validate": "https://lottie.host/c5c16573-0479-4d89-9388-37207865768e/P1W85u2r6n.json", # Check/Success
    "commit": "https://lottie.host/c5c16573-0479-4d89-9388-37207865768e/P1W85u2r6n.json",   # Success
    "reflect": "https://lottie.host/0a068406-880c-4806-b33c-3647321e0649/m8K8yR2u2M.json",  # Thinking again
    "fail": "https://lottie.host/3a479482-5369-4505-8968-385011707572/L53069152n.json"     # Error
}

# Use a generic fallback if these specific IDs don't resolve (simulated for now since we can't browse dynamic IDs easily)
# In production we would host these locally.
# Let's use a helper to load or return None
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# --- Sidebar ---
st.sidebar.title("🤖 XTeam Agents")
st.sidebar.info("Cognitive Operating System Monitor")

page = st.sidebar.radio("Navigation", ["Overview", "Live Agents", "Chat", "Tasks", "Workspace", "Brain Inspector", "Knowledge Graph", "Audit Log"])

st.sidebar.markdown("---")
st.sidebar.subheader("Actions")

with st.sidebar.form("new_task_form"):
    st.write("Submit New Task")
    task_desc = st.text_area("Description", height=100)
    task_priority = st.slider("Priority", 1, 5, 3)
    submitted = st.form_submit_button("Submit Task")
    
    if submitted and task_desc:
        try:
            res = requests.post(
                f"{MCP_SERVER_URL}/api/tasks",
                json={"description": task_desc, "priority": task_priority}
            )
            if res.status_code == 200:
                st.sidebar.success(f"Task submitted: {res.json().get('task_id')}")
            else:
                st.sidebar.error(f"Error: {res.text}")
        except Exception as e:
            st.sidebar.error(f"Connection failed: {e}")

# --- Database Connections ---

def get_db_connection():
    # Disable cache to avoid transaction errors
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        database="xteam",
        user="postgres",
        password=os.environ.get("POSTGRES_PASSWORD", "xteam_password")
    )

@st.cache_resource
def get_neo4j_driver():
    return GraphDatabase.driver(
        os.environ.get("NEO4J_URL", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "xteam_password"))
    )

# --- Pages ---

def show_workspace():
    st.title("Workspace Explorer")
    st.info("Browse and view files in the agent workspace.")
    
    # State for current path
    if "current_path" not in st.session_state:
        st.session_state.current_path = "."
    
    # Breadcrumbs / Up button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.code(f"/app/workspace/{st.session_state.current_path}")
    with col2:
        if st.session_state.current_path != ".":
            if st.button("⬆️ Up"):
                # Simple logic to go up one level
                parts = st.session_state.current_path.split("/")
                if len(parts) > 1:
                    st.session_state.current_path = "/".join(parts[:-1])
                else:
                    st.session_state.current_path = "."
                st.rerun()

    # List files
    try:
        res = requests.get(f"{MCP_SERVER_URL}/api/files/list", params={"path": st.session_state.current_path})
        if res.status_code == 200:
            data = res.json()
            entries = data.get("entries", [])
            
            for entry in entries:
                col_icon, col_name, col_size, col_action = st.columns([0.5, 3, 1, 1])
                is_dir = entry["type"] == "directory"
                
                with col_icon:
                    st.write("Fn" if is_dir else "📄")
                with col_name:
                    if is_dir:
                        if st.button(f"{entry['name']}/", key=f"dir_{entry['name']}"):
                            if st.session_state.current_path == ".":
                                st.session_state.current_path = entry['name']
                            else:
                                st.session_state.current_path = f"{st.session_state.current_path}/{entry['name']}"
                            st.rerun()
                    else:
                        st.write(entry['name'])
                with col_size:
                    if not is_dir and entry['size'] is not None:
                        st.write(f"{entry['size']} B")
                with col_action:
                    if not is_dir:
                        if st.button("View", key=f"view_{entry['name']}"):
                            # Read file content
                            file_path = f"{st.session_state.current_path}/{entry['name']}" if st.session_state.current_path != "." else entry['name']
                            file_res = requests.get(f"{MCP_SERVER_URL}/api/files/read", params={"path": file_path})
                            if file_res.status_code == 200:
                                st.session_state.selected_file_content = file_res.json().get("content", "")
                                st.session_state.selected_file_name = entry['name']
                            else:
                                st.error(f"Error reading file: {file_res.text}")

        else:
            st.error(f"Failed to list files: {res.text}")
    except Exception as e:
        st.error(f"Connection error: {e}")

    # File Viewer
    if "selected_file_content" in st.session_state:
        st.divider()
        st.subheader(f"Viewing: {st.session_state.selected_file_name}")
        st.code(st.session_state.selected_file_content, language="python") # Defaulting to python highlighting
        if st.button("Close Viewer"):
            del st.session_state.selected_file_content
            del st.session_state.selected_file_name
            st.rerun()

def show_live_agents():
    st.title("Live Cognitive Graph")
    
    conn = get_db_connection()
    
    # 1. Select Active Task
    cur = conn.cursor()
    cur.execute("""
        SELECT task_id, description, status 
        FROM tasks 
        WHERE status IN ('pending', 'analyzing', 'planning', 'executing', 'validating') 
        ORDER BY created_at DESC
    """)
    active_tasks = cur.fetchall()
    
    if not active_tasks:
        st.info("No active tasks running currently.")
        # Allow selecting completed tasks for replay/review
        cur.execute("SELECT task_id, description, status FROM tasks ORDER BY created_at DESC LIMIT 10")
        recent_tasks = cur.fetchall()
        task_options = {f"{t[0]} ({t[2]})": t[0] for t in recent_tasks}
    else:
        task_options = {f"{t[0]} ({t[2]}) - {t[1][:30]}...": t[0] for t in active_tasks}
    
    selected_option = st.selectbox("Select Task to Monitor", list(task_options.keys()))
    
    if selected_option:
        task_id = task_options[selected_option]
        
        col1, col2, col3 = st.columns([1.5, 2, 1.5])
        
        with col1:
            st.subheader("Agent State")
            
            # Get latest node from audit log
            cur.execute("""
                SELECT node_name, event_type 
                FROM audit_log 
                WHERE task_id = %s AND event_type IN ('node_entered', 'node_exited', 'task_failed', 'task_completed')
                ORDER BY timestamp DESC LIMIT 1
            """, (task_id,))
            last_event = cur.fetchone()
            current_node = last_event[0] if last_event else "analyze" # Default to analyze start
            
            # Handle fail state
            if last_event and last_event[1] == 'task_failed':
                current_node = "fail"
            
            # Display Lottie
            lottie_url = LOTTIE_URLS.get(current_node, LOTTIE_URLS["analyze"])
            lottie_json = load_lottie_url(lottie_url)
            
            if lottie_json:
                st_lottie(lottie_json, height=300, key="agent_anim")
            else:
                st.image("https://via.placeholder.com/300x300.png?text=Agent+Working", caption="Agent Animation")
            
            st.markdown(f"<h3 style='text-align: center; color: #3fb950;'>Current Phase: {current_node.upper()}</h3>", unsafe_allow_html=True)
            
        with col2:
            st.subheader("Cognitive Map")
            # Graphviz Chart (Styled)
            graph = graphviz.Digraph()
            graph.attr(rankdir='LR', bgcolor='#0d1117')
            graph.attr('node', shape='box', style='filled', fontname='Inter', fontcolor='white')
            graph.attr('edge', color='#30363d')
            
            nodes = ["analyze", "plan", "execute", "validate", "commit", "reflect"]
            
            for node in nodes:
                color = "#161b22" # Default inactive
                pencolor = "#30363d"
                
                if node == current_node:
                    color = "#238636" # Active Green
                    pencolor = "#3fb950"
                elif node == "fail" and current_node == "fail":
                     # Special case if we had a fail node in graph, but we don't, we just color current
                     pass

                graph.node(node, node.upper(), fillcolor=color, color=pencolor)
            
            # Edges
            graph.edge("analyze", "plan")
            graph.edge("plan", "execute")
            graph.edge("execute", "validate")
            graph.edge("validate", "commit", label="ok")
            graph.edge("validate", "plan", label="fail", style="dashed")
            graph.edge("commit", "reflect")
            graph.edge("validate", "reflect", label="max_retries", style="dashed")
            
            st.graphviz_chart(graph, use_container_width=True)
            
        with col3:
            st.subheader("Live Terminal")
            # Poll audit logs
            cur.execute("""
                SELECT timestamp, node_name, description, data
                FROM audit_log 
                WHERE task_id = %s
                ORDER BY timestamp DESC LIMIT 20
            """, (task_id,))
            logs = cur.fetchall()
            
            for log in logs:
                agent_name = log[1] if log[1] else "system"
                st.code(f"[{log[0].strftime('%H:%M:%S')}] {agent_name.upper()}\n{log[2]}", language="bash")

def show_brain_inspector():
    st.title("Brain Inspector")
    st.info("Debug and verify the system's memory.")

    tab1, tab2 = st.tabs(["Semantic Memory (Knowledge)", "Episodic Memory (Chat)"])
    
    with tab1:
        st.subheader("Semantic Search Playground")
        query = st.text_input("Search Query", placeholder="e.g., 'Docker guidelines'")
        if query:
            try:
                res = requests.get(f"{MCP_SERVER_URL}/api/memory/search", params={"query": query})
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    if results:
                        for idx, r in enumerate(results):
                            with st.expander(f"Result #{idx+1} (Type: {r.get('metadata', {}).get('type', 'unknown')})"):
                                st.write(r.get("content"))
                                st.json(r.get("metadata"))
                    else:
                        st.warning("No results found.")
                else:
                    st.error(f"Search failed: {res.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")
                
    with tab2:
        st.subheader("Episodic Trace")
        st.write("View raw conversation history for a task.")
        # We can reuse the task detail view logic here or enhance it
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT task_id, description FROM tasks ORDER BY created_at DESC LIMIT 50")
        tasks = cur.fetchall()
        task_map = {f"{t[0]} - {t[1][:30]}...": t[0] for t in tasks}
        
        selected_task = st.selectbox("Select Task", list(task_map.keys()))
        if selected_task:
            t_id = task_map[selected_task]
            # In a real system, we'd query Redis directly via API. 
            # For now, we fall back to audit log which captures the interactions
            cur.execute("""
                SELECT timestamp, agent_name, description, data
                FROM audit_log 
                WHERE task_id = %s AND event_type IN ('llm_request', 'llm_response', 'tool_call', 'tool_result')
                ORDER BY timestamp ASC
            """, (t_id,))
            logs = cur.fetchall()
            
            for log in logs:
                role = "🤖 Assistant" if "response" in log[2] or "tool_call" in log[2] else "👤 User/System"
                with st.chat_message(role):
                    st.write(f"**{log[1]}** ({log[0].strftime('%H:%M:%S')})")
                    st.write(log[2])
                    if log[3]:
                        st.json(log[3])

def show_chat():
    st.title("Chat with System")
    st.info("Ask questions about the system state, knowledge base, or general queries.")
    
    # Chat history state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response from API
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                res = requests.post(f"{MCP_SERVER_URL}/api/chat", json={"message": prompt})
                if res.status_code == 200:
                    response_text = res.json().get("response", "No response.")
                    message_placeholder.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                else:
                    error_msg = f"Error: {res.text}"
                    message_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Connection failed: {e}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

def show_overview():
    st.title("System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total Tasks
        cur.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cur.fetchone()[0]
        col1.metric("Total Tasks", total_tasks)
        
        # Active Tasks
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('pending', 'analyzing', 'planning', 'executing', 'validating')")
        active_tasks = cur.fetchone()[0]
        col2.metric("Active Tasks", active_tasks)
        
        # Completed Tasks
        cur.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
        completed_tasks = cur.fetchone()[0]
        col3.metric("Completed Tasks", completed_tasks)
        
        # Recent Activity
        st.subheader("Recent Activity")
        cur.execute("""
            SELECT timestamp, agent_name, event_type, description 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        audit_data = cur.fetchall()
        df = pd.DataFrame(audit_data, columns=["Time", "Agent", "Event", "Description"])
        st.dataframe(df)
        
        # --- Analytics Charts ---
        st.divider()
        st.subheader("System Analytics")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.write("**Tasks by Status**")
            cur.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            status_data = cur.fetchall()
            if status_data:
                status_df = pd.DataFrame(status_data, columns=["Status", "Count"])
                st.bar_chart(status_df.set_index("Status"))
            else:
                st.info("No data for chart.")
                
        with col_chart2:
            st.write("**Activity Volume (Last 24h)**")
            cur.execute("""
                SELECT date_trunc('hour', timestamp) as hour, COUNT(*) 
                FROM audit_log 
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                GROUP BY hour 
                ORDER BY hour
            """)
            activity_data = cur.fetchall()
            if activity_data:
                activity_df = pd.DataFrame(activity_data, columns=["Hour", "Events"])
                st.line_chart(activity_df.set_index("Hour"))
            else:
                st.info("No data for chart.")
        
        cur.close()
    except Exception as e:
        st.error(f"Database error: {e}")

def show_tasks():
    st.title("Task Management")
    
    conn = get_db_connection()
    query = "SELECT task_id, description, status, created_at, updated_at FROM tasks ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn)
    
    # Add Actions column
    st.dataframe(df)

    st.subheader("Manage Task")
    col1, col2 = st.columns([3, 1])
    with col1:
        task_id_action = st.text_input("Task ID to Cancel/Delete:")
    with col2:
        st.write("")
        st.write("")
        if st.button("Cancel Task", type="primary"):
            if task_id_action:
                try:
                    res = requests.post(f"{MCP_SERVER_URL}/api/tasks/{task_id_action}/cancel")
                    if res.status_code == 200:
                        st.success(f"Task {task_id_action} cancelled")
                    else:
                        st.error(f"Failed to cancel: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Task Detail View
    selected_task_id = st.text_input("Enter Task ID for details:", key="detail_view")
    if selected_task_id:
        st.subheader(f"Task Details: {selected_task_id}")
        
        # Get task state from audit log (simplified reconstruction)
        cur = conn.cursor()
        cur.execute("""
            SELECT timestamp, agent_name, event_type, description, data
            FROM audit_log 
            WHERE task_id = %s
            ORDER BY timestamp ASC
        """, (selected_task_id,))
        
        events = cur.fetchall()
        for event in events:
            with st.expander(f"{event[0]} - {event[1]} - {event[2]}"):
                st.write(event[3])
                if event[4]:
                    st.json(event[4])

def show_knowledge_graph():
    st.title("Knowledge Graph")
    st.info("Visualizing procedural memory from Neo4j")
    
    try:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Get summary stats
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            st.metric("Total Knowledge Nodes", node_count)
            
            # Simple visualization (Tabular for now, could be graphviz)
            st.subheader("Recent Knowledge Nodes")
            result = session.run("""
                MATCH (n) 
                RETURN labels(n) as labels, 
                       coalesce(n.description, substring(n.content, 0, 100)) as description, 
                       toString(n.created_at) as created_at 
                ORDER BY created_at DESC LIMIT 20
            """)
            data = [r.data() for r in result]
            if data:
                st.dataframe(pd.DataFrame(data))
            else:
                st.write("No knowledge nodes found.")
                
    except Exception as e:
        st.error(f"Neo4j error: {e}")

def show_audit_log():
    st.title("System Audit Log")
    
    conn = get_db_connection()
    query = "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100"
    df = pd.read_sql_query(query, conn)
    
    st.dataframe(df)

# --- Routing ---

if page == "Overview":
    show_overview()
elif page == "Live Agents":
    show_live_agents()
elif page == "Chat":
    show_chat()
elif page == "Tasks":
    show_tasks()
elif page == "Workspace":
    show_workspace()
elif page == "Brain Inspector":
    show_brain_inspector()
elif page == "Knowledge Graph":
    show_knowledge_graph()
elif page == "Audit Log":
    show_audit_log()
