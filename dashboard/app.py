import streamlit as st
from streamlit_autorefresh import st_autorefresh
import psycopg2
import pandas as pd
import os
import time
from datetime import datetime
from neo4j import GraphDatabase

# Configuration
st.set_page_config(
    page_title="XTeam Agents Dashboard",
    page_icon="🤖",
    layout="wide",
)

# Auto refresh every 5 seconds
st_autorefresh(interval=5000, key="data_refresh")

# --- Sidebar ---
st.sidebar.title("🤖 XTeam Agents")
st.sidebar.info("Cognitive Operating System Monitor")

page = st.sidebar.radio("Navigation", ["Overview", "Tasks", "Knowledge Graph", "Audit Log"])

# --- Database Connections ---

def get_db_connection():
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
        st.dataframe(df, use_container_width=True)
        
        cur.close()
    except Exception as e:
        st.error(f"Database error: {e}")

def show_tasks():
    st.title("Task Management")
    
    conn = get_db_connection()
    query = "SELECT task_id, description, status, created_at, updated_at FROM tasks ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn)
    
    st.dataframe(df, use_container_width=True)
    
    # Task Detail View
    selected_task_id = st.text_input("Enter Task ID for details:")
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
    
    st.dataframe(df, use_container_width=True)

# --- Routing ---

if page == "Overview":
    show_overview()
elif page == "Tasks":
    show_tasks()
elif page == "Knowledge Graph":
    show_knowledge_graph()
elif page == "Audit Log":
    show_audit_log()
