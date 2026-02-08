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

# --- Custom CSS (Ultra-Modern Cyberpunk/Glassmorphism) ---
st.markdown("""
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* CSS Variables */
    :root {
        /* Neon Accents */
        --neon-green: #00ff9f;
        --neon-pink: #ff006e;
        --neon-cyan: #00d9ff;
        --neon-blue: #58a6ff;

        /* Dark Backgrounds */
        --bg-primary: #0a0e1a;
        --bg-secondary: #0e1525;
        --bg-tertiary: #161d2f;

        /* Glassmorphism */
        --glass-bg: rgba(22, 29, 47, 0.7);
        --glass-border: rgba(88, 166, 255, 0.2);
    }

    /* Hide Streamlit UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1rs6os, .css-17ziqus {visibility: hidden;}
    .css-1vbkxwb, .viewerBadge_container__1QSob {display: none;}

    /* Global Theme */
    .stApp {
        background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-right: 1px solid var(--glass-border);
    }

    /* Glassmorphism Cards */
    div[data-testid="stMetric"],
    div[data-testid="stExpander"],
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 20px;
        box-shadow:
            0 8px 32px rgba(0, 0, 0, 0.37),
            inset 0 0 20px rgba(88, 166, 255, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    div[data-testid="stMetric"]:hover,
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow:
            0 12px 48px rgba(0, 255, 159, 0.2),
            inset 0 0 30px rgba(88, 166, 255, 0.1);
        border-color: var(--neon-green);
    }

    /* Headers with Neon Effect */
    h1 {
        color: var(--neon-cyan) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
        text-shadow: 0 0 10px var(--neon-cyan);
    }

    h2 {
        color: var(--neon-green) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.01em;
    }

    h3 {
        color: var(--neon-blue) !important;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    /* Buttons with Neon Glow */
    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        border: 2px solid var(--neon-green);
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px rgba(0, 255, 159, 0.3);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #2ea043 0%, #238636 100%);
        box-shadow:
            0 0 20px rgba(0, 255, 159, 0.6),
            0 0 40px rgba(0, 255, 159, 0.3);
        transform: translateY(-2px);
        border-color: var(--neon-cyan);
    }

    /* Code/Terminal Blocks */
    .stCode, code, pre {
        background-color: #000000 !important;
        border: 1px solid var(--neon-green) !important;
        border-radius: 8px;
        color: #00ff9f !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        box-shadow: inset 0 0 20px rgba(0, 255, 159, 0.1);
    }

    /* Status Colors */
    .status-active, .status-executing, .status-analyzing {
        color: var(--neon-green);
        text-shadow: 0 0 10px var(--neon-green);
        font-weight: 600;
    }

    .status-error, .status-failed {
        color: #f85149;
        text-shadow: 0 0 10px #f85149;
        font-weight: 600;
    }

    .status-idle, .status-pending {
        color: #8b949e;
    }

    .status-completed {
        color: var(--neon-cyan);
        text-shadow: 0 0 10px var(--neon-cyan);
        font-weight: 600;
    }

    /* Neon Text Animation */
    .neon-text {
        color: var(--neon-green);
        text-shadow:
            0 0 5px var(--neon-green),
            0 0 10px var(--neon-green),
            0 0 20px var(--neon-green);
        animation: flicker 3s infinite alternate;
    }

    @keyframes flicker {
        0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% { opacity: 1; }
        20%, 24%, 55% { opacity: 0.85; }
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
        border-radius: 6px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--neon-green), var(--neon-cyan));
        border-radius: 6px;
        border: 2px solid var(--bg-primary);
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-pink));
    }

    /* Dataframes */
    [data-testid="stDataFrame"] {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        font-weight: 700;
        color: var(--neon-green) !important;
    }

    /* Reduced Motion */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }

    /* Fallback for browsers without backdrop-filter */
    @supports not (backdrop-filter: blur(10px)) {
        .glass-card,
        div[data-testid="stMetric"],
        [data-testid="stSidebar"] {
            background: var(--bg-tertiary);
        }
    }
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

# Enhanced Lottie loader with timeout and better error handling
def load_lottie_url(url: str, timeout: int = 5):
    """
    Load Lottie animation from URL with timeout and error handling.

    Args:
        url: URL to Lottie JSON file
        timeout: Request timeout in seconds

    Returns:
        Lottie JSON dict or None if failed
    """
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.json()
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return None

def get_agent_emoji(agent_state: str) -> str:
    """Get emoji representation for agent state"""
    emoji_map = {
        "analyze": "🔍",
        "plan": "📋",
        "execute": "⚡",
        "validate": "✅",
        "commit": "💾",
        "reflect": "🤔",
        "fail": "❌"
    }
    return emoji_map.get(agent_state, "🤖")

def get_agent_color(agent_name: str) -> str:
    """Return neon color for agent"""
    color_map = {
        "analyze": "#00d9ff",  # Cyan
        "plan": "#00ff9f",     # Green
        "execute": "#ff006e",  # Pink
        "validate": "#58a6ff", # Blue
        "commit": "#00ff9f",   # Green
        "reflect": "#00d9ff",  # Cyan
        "fail": "#f85149",     # Red
        "system": "#8b949e"    # Gray
    }
    return color_map.get(agent_name.lower(), "#ffffff")

def render_agent_animation(agent_state: str, size: int = 450):
    """
    Render agent animation with loading state and fallback.

    Args:
        agent_state: Current agent state (analyze, plan, execute, etc.)
        size: Animation height in pixels
    """
    import time

    lottie_url = LOTTIE_URLS.get(agent_state, LOTTIE_URLS["analyze"])

    # Loading placeholder
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <div class="loading-spinner">🔄</div>
            <p style="color: var(--neon-cyan);">Loading animation...</p>
        </div>
        <style>
        .loading-spinner {
            font-size: 48px;
            animation: spin 2s linear infinite;
        }
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)

    # Load animation
    lottie_json = load_lottie_url(lottie_url)

    if lottie_json:
        placeholder.empty()
        # Render with glow effect
        st.markdown(f"""
        <div class="animation-container" style="
            padding: 30px;
            border-radius: 20px;
            background: radial-gradient(circle, rgba(0,255,159,0.15) 0%, transparent 70%);
            text-align: center;
        ">
        """, unsafe_allow_html=True)

        st_lottie(
            lottie_json,
            height=size,
            key=f"agent_{agent_state}_{int(time.time() * 1000)}",
            speed=1.0,
            loop=True,
            quality="high"
        )

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        # CSS-animated emoji fallback
        placeholder.empty()
        emoji = get_agent_emoji(agent_state)
        st.markdown(f"""
        <div class="agent-fallback" style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: {size}px;
            position: relative;
        ">
            <div class="agent-pulse"></div>
            <div class="agent-emoji">{emoji}</div>
            <p class="fallback-text">Animation unavailable</p>
        </div>
        <style>
        .agent-emoji {{
            font-size: 150px;
            animation: float 3s ease-in-out infinite;
            position: relative;
            z-index: 2;
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0) rotate(0deg); }}
            25% {{ transform: translateY(-15px) rotate(5deg); }}
            75% {{ transform: translateY(-15px) rotate(-5deg); }}
        }}
        .agent-pulse {{
            position: absolute;
            width: 250px;
            height: 250px;
            border-radius: 50%;
            background: radial-gradient(circle, var(--neon-green) 0%, transparent 70%);
            opacity: 0.3;
            animation: pulse 2s ease-in-out infinite;
            z-index: 1;
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(0.8); opacity: 0.2; }}
            50% {{ transform: scale(1.3); opacity: 0.5); }}
        }}
        .fallback-text {{
            color: var(--neon-cyan);
            font-size: 14px;
            margin-top: 20px;
            font-family: 'Inter', sans-serif;
        }}
        </style>
        """, unsafe_allow_html=True)

def render_mission_control_header(task_id: str, task_status: str):
    """
    Render mission control status bar with system stats.

    Args:
        task_id: Current task ID
        task_status: Current task status
    """
    # Calculate uptime (simplified - could use actual system start time)
    uptime = "24:35:12"  # TODO: Calculate from system start

    # System status indicator
    system_status = "🟢 OPERATIONAL"

    st.markdown(f"""
    <div class="mission-control-header glass-card">
        <div class="mc-section">
            <span class="mc-label">◉ MISSION ID</span>
            <span class="mc-value neon-text">{task_id[:12]}</span>
        </div>
        <div class="mc-divider"></div>
        <div class="mc-section">
            <span class="mc-label">◉ STATUS</span>
            <span class="mc-value status-{task_status.lower()}">{task_status.upper()}</span>
        </div>
        <div class="mc-divider"></div>
        <div class="mc-section">
            <span class="mc-label">◉ UPTIME</span>
            <span class="mc-value">{uptime}</span>
        </div>
        <div class="mc-divider"></div>
        <div class="mc-section">
            <span class="mc-label">◉ SYSTEM</span>
            <span class="mc-value">{system_status}</span>
        </div>
    </div>
    <style>
    .mission-control-header {{
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 25px 20px;
        margin-bottom: 30px;
        border: 2px solid var(--glass-border);
        box-shadow:
            0 4px 30px rgba(0, 255, 159, 0.1),
            inset 0 0 20px rgba(0, 217, 255, 0.05);
    }}
    .mc-section {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        flex: 1;
    }}
    .mc-divider {{
        width: 1px;
        height: 50px;
        background: linear-gradient(
            to bottom,
            transparent,
            var(--neon-cyan),
            transparent
        );
    }}
    .mc-label {{
        font-size: 10px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 600;
    }}
    .mc-value {{
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }}
    </style>
    """, unsafe_allow_html=True)

def render_matrix_terminal(logs: list):
    """
    Render logs in Matrix-style terminal with color coding.

    Args:
        logs: List of tuples (timestamp, agent_name, description, data)
    """
    st.markdown('<div class="matrix-terminal">', unsafe_allow_html=True)

    if not logs:
        st.markdown('<p class="no-logs">No activity logged yet...</p>', unsafe_allow_html=True)
    else:
        for log in logs:
            timestamp = log[0].strftime('%H:%M:%S.%f')[:-3]  # Millisecond precision
            agent = (log[1] or "system").upper()
            message = log[2]

            # Get color for agent
            color = get_agent_color(log[1].lower() if log[1] else "system")

            # Truncate long messages
            if len(message) > 80:
                message = message[:77] + "..."

            st.markdown(f"""
            <div class="terminal-line">
                <span class="timestamp">[{timestamp}]</span>
                <span class="agent-name" style="color: {color};">{agent:12s}</span>
                <span class="message">{message}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Add terminal styling
    st.markdown("""
    <style>
    .matrix-terminal {
        background: #000000;
        border: 2px solid var(--neon-green);
        border-radius: 8px;
        padding: 15px;
        max-height: 520px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        box-shadow:
            inset 0 0 30px rgba(0, 255, 159, 0.1),
            0 0 20px rgba(0, 255, 159, 0.2);
        position: relative;
    }

    .terminal-line {
        margin: 8px 0;
        font-size: 12px;
        line-height: 1.8;
        animation: fadeInTerminal 0.3s ease-in;
        display: flex;
        gap: 10px;
    }

    @keyframes fadeInTerminal {
        from {
            opacity: 0;
            transform: translateX(-10px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .timestamp {
        color: #6e7681;
        flex-shrink: 0;
    }

    .agent-name {
        font-weight: bold;
        flex-shrink: 0;
        text-shadow: 0 0 8px currentColor;
    }

    .message {
        color: #c9d1d9;
        flex: 1;
    }

    .no-logs {
        color: #6e7681;
        text-align: center;
        padding: 40px;
        font-style: italic;
    }

    /* Custom scrollbar for terminal */
    .matrix-terminal::-webkit-scrollbar {
        width: 8px;
    }

    .matrix-terminal::-webkit-scrollbar-track {
        background: #0a0e1a;
        border-radius: 4px;
    }

    .matrix-terminal::-webkit-scrollbar-thumb {
        background: var(--neon-green);
        border-radius: 4px;
        box-shadow: 0 0 5px var(--neon-green);
    }

    .matrix-terminal::-webkit-scrollbar-thumb:hover {
        background: var(--neon-cyan);
        box-shadow: 0 0 8px var(--neon-cyan);
    }

    /* Scanline effect (subtle) */
    .matrix-terminal::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 255, 159, 0.03) 0px,
            transparent 1px,
            transparent 2px,
            rgba(0, 255, 159, 0.03) 3px
        );
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

def render_cognitive_graph(current_node: str):
    """
    Render cognitive flow graph with enhanced neon styling.

    Args:
        current_node: Currently active node name
    """
    graph = graphviz.Digraph()
    graph.attr(rankdir='TB', bgcolor='transparent', dpi='150')
    graph.attr('node',
               shape='box',
               style='filled,rounded',
               fontname='Inter',
               fontsize='14',
               margin='0.4,0.2',
               height='0.8',
               width='1.5')
    graph.attr('edge',
               penwidth='2.5',
               arrowsize='1.0',
               fontname='Inter',
               fontsize='11')

    # Node definitions with emoji
    nodes = [
        ("analyze", "🔍\nANALYZE"),
        ("plan", "📋\nPLAN"),
        ("execute", "⚡\nEXECUTE"),
        ("validate", "✓\nVALIDATE"),
        ("commit", "💾\nCOMMIT"),
        ("reflect", "🤔\nREFLECT")
    ]

    for node_id, label in nodes:
        if node_id == current_node:
            # Active node - neon green glow
            graph.node(node_id, label,
                      fillcolor='#238636:#2ea043',  # Gradient
                      color='#00ff9f',
                      penwidth='4',
                      fontcolor='#ffffff',
                      style='filled,rounded,bold')
        else:
            # Inactive node - subtle
            graph.node(node_id, label,
                      fillcolor='#161b22',
                      color='#30363d',
                      penwidth='2',
                      fontcolor='#8b949e')

    # Edges with styled labels
    graph.edge("analyze", "plan", color='#30363d:#58a6ff')
    graph.edge("plan", "execute", color='#30363d:#58a6ff')
    graph.edge("execute", "validate", color='#30363d:#58a6ff')
    graph.edge("validate", "commit",
              label=" ✓ pass ",
              fontcolor='#3fb950',
              color='#3fb950')
    graph.edge("validate", "plan",
              label=" ⟲ replan ",
              style="dashed",
              fontcolor='#f85149',
              color='#f85149')
    graph.edge("commit", "reflect", color='#30363d:#58a6ff')

    st.graphviz_chart(graph, use_container_width=True)

# --- Sidebar ---
st.sidebar.title("🤖 XTeam Agents")
st.sidebar.info("Cognitive Operating System Monitor")

page = st.sidebar.radio("Navigation", [
    "Overview",
    "Live Agents",
    "Adversarial Team",
    "Quality Metrics",
    "MAGIC Control",
    "Chat",
    "Tasks",
    "Workspace",
    "Brain Inspector",
    "Knowledge Graph",
    "Audit Log"
])

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
    """Enhanced live cognitive graph with Mission Control layout"""
    st.title("🎯 Mission Control: Live Cognitive Graph")

    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Select Active Task
    cur.execute("""
        SELECT task_id, description, status
        FROM tasks
        WHERE status IN ('pending', 'analyzing', 'planning', 'executing', 'validating')
        ORDER BY created_at DESC
    """)
    active_tasks = cur.fetchall()

    if not active_tasks:
        st.info("No active tasks running currently. Showing recent tasks for review.")
        cur.execute("SELECT task_id, description, status FROM tasks ORDER BY created_at DESC LIMIT 10")
        recent_tasks = cur.fetchall()
        task_options = {f"{t[0]} ({t[2]})": t[0] for t in recent_tasks}
    else:
        task_options = {f"{t[0]} ({t[2]}) - {t[1][:30]}...": t[0] for t in active_tasks}

    selected_option = st.selectbox("🎯 Select Task to Monitor", list(task_options.keys()))

    if selected_option:
        task_id = task_options[selected_option]

        # Get task status
        cur.execute("SELECT status FROM tasks WHERE task_id = %s", (task_id,))
        task_status = cur.fetchone()[0]

        # Render Mission Control Header
        render_mission_control_header(task_id, task_status)

        # Get current node from audit log
        cur.execute("""
            SELECT node_name, event_type
            FROM audit_log
            WHERE task_id = %s AND event_type IN ('node_entered', 'node_exited', 'task_failed', 'task_completed')
            ORDER BY timestamp DESC LIMIT 1
        """, (task_id,))
        last_event = cur.fetchone()
        current_node = last_event[0] if last_event else "analyze"

        # Handle fail/complete states
        if last_event:
            if last_event[1] == 'task_failed':
                current_node = "fail"
            elif last_event[1] == 'task_completed':
                current_node = "commit"

        # Main 3-Panel Layout
        col_stage, col_flow, col_terminal = st.columns([2, 2.5, 2])

        # LEFT: The Stage (Agent Animation)
        with col_stage:
            st.markdown('<div class="glass-card" style="min-height: 600px;">', unsafe_allow_html=True)
            st.markdown("### 🎭 THE STAGE")

            # Render animation
            render_agent_animation(current_node, size=400)

            # Agent status display
            thinking_text = "Processing..." if current_node != "fail" else "Error Detected"
            st.markdown(f"""
            <div class="agent-status-display" style="
                text-align: center;
                margin-top: 20px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                border: 1px solid var(--neon-green);
            ">
                <h2 class="neon-text" style="margin: 0; font-size: 28px;">{current_node.upper()}</h2>
                <p style="
                    color: var(--neon-cyan);
                    margin: 10px 0 0 0;
                    font-size: 16px;
                    font-style: italic;
                ">{thinking_text}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # CENTER: The Flow (Cognitive Graph)
        with col_flow:
            st.markdown('<div class="glass-card" style="min-height: 600px;">', unsafe_allow_html=True)
            st.markdown("### 🔄 THE FLOW")

            # Render enhanced graph
            render_cognitive_graph(current_node)

            st.markdown('</div>', unsafe_allow_html=True)

        # RIGHT: The Terminal (Logs)
        with col_terminal:
            st.markdown('<div class="glass-card terminal-container" style="min-height: 600px;">', unsafe_allow_html=True)
            st.markdown("### 💻 THE TERMINAL")

            # Get logs
            cur.execute("""
                SELECT timestamp, node_name, description, data
                FROM audit_log
                WHERE task_id = %s
                ORDER BY timestamp DESC LIMIT 20
            """, (task_id,))
            logs = cur.fetchall()

            # Render matrix-style terminal
            render_matrix_terminal(logs)

            st.markdown('</div>', unsafe_allow_html=True)

    cur.close()
    conn.close()

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

def show_adversarial_team():
    st.title("🤺 Adversarial Agent Team")
    st.info("21 AI Agents working together: 1 Orchestrator + 10 Agent-Critic Pairs")

    try:
        # Get agents status
        res = requests.get(f"{MCP_SERVER_URL}/api/agents/status")
        if res.status_code == 200:
            data = res.json()
            adversarial_agents = data.get("adversarial_agents", {})

            # Overview metrics
            col1, col2, col3 = st.columns(3)
            active_count = sum(1 for a in adversarial_agents.values() if a.get("status") == "active")
            col1.metric("Total Agents", len(adversarial_agents))
            col2.metric("Active Now", active_count)
            col3.metric("Agent-Critic Pairs", 10)

            st.divider()

            # Orchestrator (Special Agent)
            st.subheader("🎯 Supreme Orchestrator")
            orch = adversarial_agents.get("orchestrator", {})
            status_color = "🟢" if orch.get("status") == "active" else "⚪"
            st.markdown(f"{status_color} **Status:** {orch.get('status', 'idle').upper()}")
            if orch.get("task_id"):
                st.code(f"Working on: {orch['task_id']}")
            st.caption("Coordinates all agents, classifies tasks, resolves conflicts")

            st.divider()

            # Agent-Critic Pairs
            st.subheader("⚔️ Agent-Critic Pairs")

            pairs = [
                ("tech_lead", "TechLead", "Strategic technical leadership", "Normal"),
                ("architect", "Architect", "System architecture & design", "Normal"),
                ("backend", "Backend", "Backend & API development", "Normal"),
                ("frontend", "Frontend", "Frontend & UX implementation", "Normal"),
                ("data", "Data", "Data engineering & ML", "Normal"),
                ("devops", "DevOps", "Infrastructure & deployment", "Normal"),
                ("qa", "QA", "Testing & quality assurance", "Perfectionist 🔍"),
                ("ai_architect", "AI Architect", "AI/ML architecture", "Normal"),
                ("security", "Security", "Security (Blue Team)", "Adversarial ⚡"),
                ("performance", "Performance", "Performance optimization", "Adversarial ⚡"),
            ]

            # Display in 2 columns
            for i in range(0, len(pairs), 2):
                col_left, col_right = st.columns(2)

                for col, pair_idx in [(col_left, i), (col_right, i+1)]:
                    if pair_idx < len(pairs):
                        agent_key, name, description, strategy = pairs[pair_idx]
                        agent_data = adversarial_agents.get(agent_key, {})

                        with col:
                            with st.container():
                                status_emoji = "🟢" if agent_data.get("status") == "active" else "⚪"
                                critic_status_emoji = "🟢" if agent_data.get("critic") == "active" else "⚪"

                                st.markdown(f"### {name}")
                                st.caption(description)
                                st.markdown(f"**Strategy:** {strategy}")
                                st.markdown(f"{status_emoji} Agent | {critic_status_emoji} Critic")

                                if agent_data.get("task_id"):
                                    st.code(f"Task: {agent_data['task_id'][:8]}...", language="text")

            st.divider()

            # Agent-Critic Debate Visualization
            st.subheader("💬 Recent Agent-Critic Debates")

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT timestamp, task_id, agent_name, description, data
                FROM audit_log
                WHERE event_type IN ('agent_proposal', 'critic_feedback', 'agent_revision')
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            debates = cur.fetchall()

            if debates:
                for debate in debates:
                    timestamp, task_id, agent, desc, data = debate

                    # Color code by event type
                    if "proposal" in desc.lower():
                        icon = "💡"
                        color = "#238636"
                    elif "feedback" in desc.lower() or "critic" in desc.lower():
                        icon = "🔍"
                        color = "#f85149"
                    else:
                        icon = "✏️"
                        color = "#58a6ff"

                    with st.expander(f"{icon} {agent} - {timestamp.strftime('%H:%M:%S')}"):
                        st.markdown(f"**Task:** `{task_id}`")
                        st.write(desc)
                        if data and isinstance(data, dict):
                            if "quality_scores" in data:
                                st.json(data["quality_scores"])
            else:
                st.info("No recent debates. Adversarial team activates on complex/critical tasks.")

            cur.close()

        else:
            st.error(f"Failed to fetch agents status: {res.text}")

    except Exception as e:
        st.error(f"Connection error: {e}")

def show_quality_metrics():
    st.title("📊 Quality Metrics Dashboard")
    st.info("5D Quality Scoring: Correctness • Completeness • Efficiency • Maintainability • Security")

    try:
        # Get quality metrics
        res = requests.get(f"{MCP_SERVER_URL}/api/metrics/quality")
        if res.status_code == 200:
            data = res.json()
            quality_data = data.get("quality_data", [])
            avg_scores = data.get("average_scores")
            total_evals = data.get("total_evaluations", 0)

            # Overview
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Evaluations", total_evals)

            if avg_scores:
                overall_avg = sum(avg_scores.values()) / len(avg_scores)
                col2.metric("Overall Quality", f"{overall_avg:.1f}/10")

                # Find best dimension
                best_dim = max(avg_scores, key=avg_scores.get)
                col3.metric("Best Dimension", best_dim.capitalize())

                st.divider()

                # 5D Radar Chart
                st.subheader("🎯 Average 5D Quality Profile")

                # Create radar chart data
                import plotly.graph_objects as go

                dimensions = ["Correctness", "Completeness", "Efficiency", "Maintainability", "Security"]
                values = [
                    avg_scores.get("correctness", 0),
                    avg_scores.get("completeness", 0),
                    avg_scores.get("efficiency", 0),
                    avg_scores.get("maintainability", 0),
                    avg_scores.get("security", 0),
                ]

                fig = go.Figure()

                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],  # Close the polygon
                    theta=dimensions + [dimensions[0]],
                    fill='toself',
                    name='Quality Profile',
                    line=dict(color='#3fb950', width=2),
                    fillcolor='rgba(63, 185, 80, 0.3)'
                ))

                # Threshold line (approval threshold = 7.0)
                threshold_values = [7.0] * (len(dimensions) + 1)
                fig.add_trace(go.Scatterpolar(
                    r=threshold_values,
                    theta=dimensions + [dimensions[0]],
                    mode='lines',
                    name='Approval Threshold (7.0)',
                    line=dict(color='#f85149', width=1, dash='dash')
                ))

                fig.update_layout(
                    polar=dict(
                        bgcolor='#0d1117',
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10],
                            gridcolor='#30363d',
                            tickfont=dict(color='#c9d1d9')
                        ),
                        angularaxis=dict(
                            gridcolor='#30363d',
                            tickfont=dict(color='#c9d1d9')
                        )
                    ),
                    paper_bgcolor='#0d1117',
                    plot_bgcolor='#0d1117',
                    font=dict(color='#c9d1d9'),
                    showlegend=True,
                    legend=dict(
                        bgcolor='#161b22',
                        bordercolor='#30363d',
                        borderwidth=1
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # Dimension Breakdown
                st.subheader("📈 Quality Dimensions Breakdown")

                col1, col2 = st.columns(2)

                with col1:
                    # Bar chart
                    import plotly.express as px
                    df_scores = pd.DataFrame({
                        'Dimension': dimensions,
                        'Score': values
                    })

                    fig_bar = px.bar(
                        df_scores,
                        x='Dimension',
                        y='Score',
                        color='Score',
                        color_continuous_scale=['#f85149', '#ffa657', '#3fb950'],
                        range_color=[0, 10]
                    )
                    fig_bar.update_layout(
                        paper_bgcolor='#0d1117',
                        plot_bgcolor='#0d1117',
                        font=dict(color='#c9d1d9'),
                        yaxis=dict(range=[0, 10])
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col2:
                    st.write("**Score Interpretation:**")
                    st.markdown("""
                    - **9-10**: Excellent ✨
                    - **7-8**: Good ✅
                    - **5-6**: Acceptable ⚠️
                    - **< 5**: Needs Improvement ❌

                    **Approval Threshold:** 7.0

                    Tasks with average score below 7.0 trigger replanning.
                    """)

                st.divider()

                # Recent Evaluations
                st.subheader("🕒 Recent Quality Evaluations")

                if quality_data:
                    for item in quality_data[:10]:  # Show last 10
                        scores = item["scores"]
                        avg_score = sum(scores.values()) / len(scores)

                        # Color based on score
                        if avg_score >= 8:
                            badge_color = "🟢"
                        elif avg_score >= 6:
                            badge_color = "🟡"
                        else:
                            badge_color = "🔴"

                        with st.expander(f"{badge_color} Task {item['task_id'][:8]}... | Avg: {avg_score:.1f}/10 | {item['agent']}"):
                            st.caption(f"Evaluated at: {item['timestamp']}")

                            cols = st.columns(5)
                            for idx, (dim, score) in enumerate(scores.items()):
                                with cols[idx]:
                                    st.metric(dim.capitalize(), f"{score:.1f}")
                else:
                    st.info("No quality evaluations recorded yet.")
            else:
                st.warning("No quality metrics available. Quality scoring activates when adversarial team is used.")
        else:
            st.error(f"Failed to fetch quality metrics: {res.text}")

    except Exception as e:
        st.error(f"Connection error: {e}")

def show_magic_control():
    st.title("MAGIC Control Center")
    st.info("Human-Machine Artificial General Intelligence Core - Human-AI Collaboration")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Pending Escalations",
        "Active Sessions",
        "Confidence Dashboard",
        "Feedback & Learning",
        "Evolution Metrics",
    ])

    # --- Tab 1: Pending Escalations ---
    with tab1:
        st.subheader("Pending Escalations")
        try:
            res = requests.get(f"{MCP_SERVER_URL}/api/magic/escalations")
            if res.status_code == 200:
                data = res.json()
                if not data.get("magic_enabled", False):
                    st.warning("MAGIC system is not enabled. Set MAGIC_ENABLED=true in config.")
                else:
                    escalations = data.get("escalations", [])
                    if not escalations:
                        st.success("No pending escalations. System is running autonomously.")
                    else:
                        for esc in escalations:
                            priority_colors = {
                                "critical": "#f85149",
                                "high": "#ffa657",
                                "medium": "#58a6ff",
                                "low": "#8b949e",
                            }
                            color = priority_colors.get(esc["priority"], "#ffffff")

                            with st.expander(
                                f"[{esc['priority'].upper()}] {esc['question'][:80]}...",
                                expanded=True,
                            ):
                                st.markdown(f"**Priority:** <span style='color:{color}'>{esc['priority'].upper()}</span>", unsafe_allow_html=True)
                                st.markdown(f"**Stage:** {esc['stage']}")
                                st.markdown(f"**Reason:** {esc['reason']}")
                                st.markdown(f"**Task ID:** `{esc['task_id']}`")
                                st.markdown(f"**Question:** {esc['question']}")

                                if esc.get("confidence"):
                                    conf = esc["confidence"]
                                    st.markdown(f"**Confidence:** {conf.get('overall', 'N/A')}")

                                if esc.get("options"):
                                    st.markdown("**Options:**")
                                    for opt in esc["options"]:
                                        st.markdown(f"- {opt}")

                                # Response form
                                with st.form(f"respond_{esc['id']}"):
                                    response_type = st.selectbox(
                                        "Response Type",
                                        ["approval", "rejection", "guidance", "modification", "override", "deferral"],
                                        key=f"rt_{esc['id']}",
                                    )
                                    content = st.text_area("Response", key=f"rc_{esc['id']}")
                                    submitted = st.form_submit_button("Submit Response")

                                    if submitted:
                                        try:
                                            resp = requests.post(
                                                f"{MCP_SERVER_URL}/api/magic/escalations/{esc['id']}/respond",
                                                json={
                                                    "response_type": response_type,
                                                    "content": content,
                                                    "human_id": "dashboard",
                                                },
                                            )
                                            if resp.status_code == 200:
                                                st.success("Response submitted!")
                                                st.rerun()
                                            else:
                                                st.error(f"Error: {resp.text}")
                                        except Exception as e:
                                            st.error(f"Connection error: {e}")
            else:
                st.error(f"Failed to fetch escalations: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # --- Tab 2: Active Sessions ---
    with tab2:
        st.subheader("Active Collaborative Sessions")
        try:
            res = requests.get(f"{MCP_SERVER_URL}/api/magic/sessions")
            if res.status_code == 200:
                data = res.json()
                sessions = data.get("sessions", [])
                if not sessions:
                    st.info("No active sessions.")
                else:
                    for session in sessions:
                        with st.expander(f"Session {session['id'][:8]}... - Task {session['task_id'][:8]}..."):
                            st.markdown(f"**Status:** {session['status']}")
                            st.markdown(f"**Human:** {session['human_id']}")
                            st.markdown(f"**Created:** {session['created_at']}")

                            if session.get("messages"):
                                st.markdown("**Messages:**")
                                for msg in session["messages"]:
                                    role = msg.get("role", "system")
                                    content = msg.get("content", "")
                                    icon = "🤖" if role == "system" else "👤"
                                    st.markdown(f"{icon} **{role}:** {content}")

                            if session.get("pending_escalations"):
                                st.markdown(f"**Pending Escalations:** {len(session['pending_escalations'])}")
            else:
                st.error(f"Failed to fetch sessions: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

    # --- Tab 3: Confidence Dashboard ---
    with tab3:
        st.subheader("Confidence Scores")

        # Task selector
        conn = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT task_id, description FROM tasks ORDER BY created_at DESC LIMIT 20")
            tasks = cur.fetchall()
            cur.close()
        except Exception:
            tasks = []
        finally:
            if conn:
                conn.close()

        if tasks:
            task_map = {f"{t[0][:8]}... - {t[1][:40]}": t[0] for t in tasks}
            selected = st.selectbox("Select Task", list(task_map.keys()), key="conf_task")

            if selected:
                task_id = task_map[selected]
                try:
                    res = requests.get(f"{MCP_SERVER_URL}/api/magic/confidence/{task_id}")
                    if res.status_code == 200:
                        data = res.json()
                        scores = data.get("scores", {})

                        if scores:
                            import plotly.graph_objects as go

                            # Radar chart of latest confidence scores
                            stages = list(scores.keys())
                            overall_values = []
                            for stage in stages:
                                score = scores[stage]
                                if isinstance(score, dict):
                                    overall_values.append(score.get("overall", 0))
                                else:
                                    overall_values.append(0)

                            if stages and overall_values:
                                fig = go.Figure()
                                fig.add_trace(go.Scatterpolar(
                                    r=overall_values + [overall_values[0]],
                                    theta=stages + [stages[0]],
                                    fill='toself',
                                    name='Confidence',
                                    line=dict(color='#00ff9f', width=2),
                                    fillcolor='rgba(0, 255, 159, 0.3)',
                                ))

                                # Threshold line
                                threshold = [0.6] * (len(stages) + 1)
                                fig.add_trace(go.Scatterpolar(
                                    r=threshold,
                                    theta=stages + [stages[0]],
                                    mode='lines',
                                    name='Threshold (0.6)',
                                    line=dict(color='#f85149', width=1, dash='dash'),
                                ))

                                fig.update_layout(
                                    polar=dict(
                                        bgcolor='#0d1117',
                                        radialaxis=dict(visible=True, range=[0, 1], gridcolor='#30363d'),
                                        angularaxis=dict(gridcolor='#30363d'),
                                    ),
                                    paper_bgcolor='#0d1117',
                                    plot_bgcolor='#0d1117',
                                    font=dict(color='#c9d1d9'),
                                    showlegend=True,
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            # Detailed breakdown
                            for stage_name, score_data in scores.items():
                                if isinstance(score_data, dict):
                                    with st.expander(f"Stage: {stage_name} (Overall: {score_data.get('overall', 'N/A')})"):
                                        cols = st.columns(5)
                                        dims = ["factual_accuracy", "completeness", "relevance", "coherence", "novelty_risk"]
                                        for i, dim in enumerate(dims):
                                            with cols[i]:
                                                val = score_data.get(dim, 0)
                                                st.metric(dim.replace("_", " ").title(), f"{val:.2f}")

                                        if score_data.get("uncertainty_factors"):
                                            st.markdown("**Uncertainties:**")
                                            for uf in score_data["uncertainty_factors"]:
                                                st.markdown(f"- {uf}")
                                        if score_data.get("knowledge_gaps"):
                                            st.markdown("**Knowledge Gaps:**")
                                            for kg in score_data["knowledge_gaps"]:
                                                st.markdown(f"- {kg}")
                        else:
                            st.info("No confidence scores recorded for this task.")
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No tasks found.")

    # --- Tab 4: Feedback & Learning ---
    with tab4:
        st.subheader("Submit Feedback")

        with st.form("feedback_form"):
            fb_task_id = st.text_input("Task ID")
            fb_type = st.selectbox("Feedback Type", ["comment", "correction", "preference", "guideline", "rating"])
            fb_content = st.text_area("Feedback Content")
            fb_target = st.selectbox("Target Node", ["", "analyze", "plan", "execute", "validate"])
            fb_rating = st.slider("Rating (optional)", 0.0, 1.0, 0.5, 0.1)
            fb_persist = st.checkbox("Save as permanent guideline")
            fb_submitted = st.form_submit_button("Submit Feedback")

            if fb_submitted and fb_task_id and fb_content:
                try:
                    resp = requests.post(
                        f"{MCP_SERVER_URL}/api/magic/feedback",
                        json={
                            "task_id": fb_task_id,
                            "feedback_type": fb_type,
                            "content": fb_content,
                            "target_node": fb_target or None,
                            "rating": fb_rating,
                            "should_persist": fb_persist,
                            "human_id": "dashboard",
                        },
                    )
                    if resp.status_code == 200:
                        st.success(f"Feedback recorded: {resp.json().get('feedback_id', '')[:8]}...")
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    # --- Tab 5: Evolution Metrics ---
    with tab5:
        st.subheader("System Evolution")
        try:
            res = requests.get(f"{MCP_SERVER_URL}/api/magic/evolution")
            if res.status_code == 200:
                data = res.json()
                metrics = data.get("metrics", [])
                proposals = data.get("proposals", [])

                if metrics:
                    cols = st.columns(len(metrics))
                    for i, metric in enumerate(metrics):
                        with cols[i]:
                            trend_icon = {"improving": "^", "declining": "v", "stable": "-"}.get(metric["trend"], "-")
                            st.metric(
                                metric["name"].replace("_", " ").title(),
                                f"{metric['value']:.1%}",
                                delta=trend_icon,
                            )
                else:
                    st.info("No evolution metrics yet. Metrics accumulate as the system processes tasks with MAGIC enabled.")

                if proposals:
                    st.divider()
                    st.subheader("Improvement Proposals")
                    for prop in proposals:
                        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(prop.get("priority", ""), "")
                        with st.expander(f"{priority_icon} {prop.get('area', 'Unknown').replace('_', ' ').title()}"):
                            st.write(prop.get("proposal", ""))
            else:
                st.error(f"Failed to fetch evolution metrics: {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")


# --- Routing ---

if page == "Overview":
    show_overview()
elif page == "Live Agents":
    show_live_agents()
elif page == "Adversarial Team":
    show_adversarial_team()
elif page == "Quality Metrics":
    show_quality_metrics()
elif page == "MAGIC Control":
    show_magic_control()
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
