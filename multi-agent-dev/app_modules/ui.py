"""
UI components for the Streamlit app.
This module contains UI-related functions for the Streamlit interface.
"""
import streamlit as st
import pandas as pd
import datetime
import os
import sys
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility functions
from utils import format_timestamp, time_difference, truncate_text

def create_sidebar():
    """Create the sidebar UI elements"""
    with st.sidebar:
        st.header("Project Controls")

        if st.button("Reset System"):
            st.session_state.project_id = None
            st.session_state.tasks = []
            st.session_state.agent_logs = []
            st.session_state.requirements = ""
            st.session_state.project_outputs = {}
            st.rerun()
        
        # Claude API Configuration
        st.header("AI Configuration")
        
        # Check if required dependencies are installed
        import importlib.util
        anthropic_installed = importlib.util.find_spec("anthropic") is not None
        dotenv_installed = importlib.util.find_spec("python_dotenv") is not None
        
        if not anthropic_installed or not dotenv_installed:
            st.error("Required dependencies are missing.")
            install_commands = []
            
            if not anthropic_installed:
                install_commands.append("pip install anthropic")
            
            if not dotenv_installed:
                install_commands.append("pip install python-dotenv")
            
            st.code("\n".join(install_commands), language="bash")
            st.info("After installing the dependencies, restart the Streamlit app.")
        
        # Capture API key in session state if not already there
        if "claude_api_key" not in st.session_state:
            st.session_state.claude_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        # API key input
        api_key = st.text_input(
            "Claude API Key",
            value=st.session_state.claude_api_key,
            type="password",
            help="Enter your Anthropic API key to enable Claude for intelligent project name extraction"
        )
        
        # Update API key in session state and environment variable
        if api_key != st.session_state.claude_api_key:
            st.session_state.claude_api_key = api_key
            os.environ["ANTHROPIC_API_KEY"] = api_key
            
            # Update claude_client configuration
            try:
                from utils.llm_client import claude_client
                if hasattr(claude_client, 'configure'):
                    claude_client.configure(api_key)
                else:
                    # Set properties directly if configure method doesn't exist
                    claude_client.api_key = api_key
                    # Try to create a new client if anthropic is available
                    import importlib.util
                    if importlib.util.find_spec("anthropic") is not None:
                        from anthropic import Anthropic
                        claude_client.client = Anthropic(api_key=api_key)
            except Exception as e:
                st.error(f"Error configuring Claude client: {str(e)}")

def render_agent_logs():
    """Render the agent logs section"""
    st.header("Agent Activity")
    
    if "agent_logs" in st.session_state and st.session_state.agent_logs:
        logs = st.session_state.agent_logs
        
        # Group logs by agent
        agent_types = sorted(set(log["agent"] for log in logs))
        
        # Create tabs for each agent type plus "All"
        tabs = ["All"] + agent_types
        selected_tab = st.tabs(tabs)
        
        for i, tab in enumerate(tabs):
            with selected_tab[i]:
                if tab == "All":
                    filtered_logs = logs
                else:
                    filtered_logs = [log for log in logs if log["agent"] == tab]
                
                if filtered_logs:
                    for log in reversed(filtered_logs):
                        with st.container():
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                st.caption(format_timestamp(log["timestamp"]))
                            with col2:
                                st.markdown(log["message"])
                            st.divider()
                else:
                    st.info(f"No logs for {tab}.")
    else:
        st.info("No agent activity logged yet.")

def render_task_list():
    """Render the task list section"""
    st.header("Tasks")
    
    if "tasks" in st.session_state and st.session_state.tasks:
        # Convert tasks to DataFrame
        tasks_df = pd.DataFrame(st.session_state.tasks)
        
        # Add status column if not present
        if "status" not in tasks_df.columns:
            tasks_df["status"] = "pending"
        
        # Calculate progress
        total_tasks = len(tasks_df)
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "completed")
        in_progress_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "in_progress")
        pending_tasks = total_tasks - completed_tasks - in_progress_tasks
        
        # Display progress metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tasks", total_tasks)
        with col2:
            st.metric("Completed", completed_tasks)
        with col3:
            st.metric("In Progress", in_progress_tasks)
        
        # Progress bar
        if total_tasks > 0:
            progress = completed_tasks / total_tasks
            st.progress(progress)
        
        # Display tasks
        for i, task in enumerate(st.session_state.tasks):
            with st.expander(f"{i+1}. {task.get('title', 'Untitled Task')}"):
                st.write(f"**Description:** {task.get('description', 'No description')}")
                st.write(f"**Assigned Agent:** {task.get('assigned_agent', 'None')}")
                
                # Task status
                status = task.get("status", "pending")
                if status == "completed":
                    st.success("Status: Completed")
                elif status == "in_progress":
                    st.info("Status: In Progress")
                else:
                    st.warning("Status: Pending")
                
                # Run task button
                if status != "completed":
                    if st.button(f"Run Task", key=f"run_task_{i}"):
                        from app_modules.task_execution import run_task
                        result = run_task(task["id"])
                        st.success("Task execution complete!")
                        st.rerun()  # Using st.rerun() instead of experimental_rerun()
    else:
        st.info("No tasks created yet. Enter project requirements to get started.")

def render_project_output():
    """Render the project output section"""
    if "project_id" in st.session_state and st.session_state.project_id:
        st.header("Project Output")
        
        # Find project directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        projects_dir = os.path.join(base_dir, "projects")
        
        # List all projects
        if os.path.exists(projects_dir):
            project_folders = [d for d in os.listdir(projects_dir) 
                            if os.path.isdir(os.path.join(projects_dir, d))]
            
            if project_folders:
                # Find the most recently modified project
                latest_project = max(project_folders, 
                                    key=lambda d: os.path.getmtime(os.path.join(projects_dir, d)))
                
                project_path = os.path.join(projects_dir, latest_project)
                
                st.success(f"Project created: {latest_project}")
                
                # Display project structure
                if os.path.exists(project_path):
                    with st.expander("Project Structure"):
                        st.text(_get_directory_tree(project_path))
                    
                    # Open in VS Code button
                    if st.button("Open in VS Code"):
                        try:
                            os.system(f"code \"{project_path}\"")
                            st.success(f"Opened {latest_project} in VS Code")
                        except Exception as e:
                            st.error(f"Error opening VS Code: {str(e)}")
                            st.error("VS Code command 'code' not found. Make sure VS Code is installed and the command is in your PATH.")
    else:
        st.info("No applications created yet. Run tasks to generate complete applications.")

def _get_directory_tree(path, indent="", is_last=True, exclude_dirs=None):
    """Generate a directory tree string"""
    exclude_dirs = exclude_dirs or [".git", "__pycache__", "node_modules"]
    
    if os.path.isdir(path):
        basename = os.path.basename(path)
        
        if basename in exclude_dirs:
            return ""
        
        result = f"{indent}{'└── ' if is_last else '├── '}{basename}/\n"
        
        items = [i for i in sorted(os.listdir(path)) 
                if not i.startswith('.') and i not in exclude_dirs]
        
        indent_increased = indent + ('    ' if is_last else '│   ')
        
        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1)
            item_path = os.path.join(path, item)
            result += _get_directory_tree(item_path, indent_increased, is_last_item, exclude_dirs)
            
        return result
    else:
        basename = os.path.basename(path)
        return f"{indent}{'└── ' if is_last else '├── '}{basename}\n"