import streamlit as st
import pandas as pd
import time
import json
import os
import uuid
import sys
import traceback
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from core.database import DatabaseConnector
from core.orchestration_simple import SimpleOrchestrator, SystemState, AgentState, Message
from utils import format_timestamp, time_difference, truncate_text, set_log_function, log_agent_activity
from utils.llm_client import claude_client

# Fallback to the local implementation if needed
from get_project_name import get_project_name_from_requirements

# Import app modules
from app_modules.ui import create_sidebar, render_agent_logs, render_task_list, render_project_output
from app_modules.task_execution import run_task

# Page configuration
st.set_page_config(
    page_title="AI Development Team",
    page_icon="🚀",
    layout="wide",
)

# Initialize database connection
db_connector = DatabaseConnector()

# Initialize session state
if "project_id" not in st.session_state:
    st.session_state.project_id = None
    
if "project_name" not in st.session_state:
    st.session_state.project_name = None
    
if "tasks" not in st.session_state:
    st.session_state.tasks = []
    
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []
    
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = SimpleOrchestrator(db_connector=db_connector)
    
if "requirements" not in st.session_state:
    st.session_state.requirements = ""
    
if "project_outputs" not in st.session_state:
    st.session_state.project_outputs = {}

# Function to log agent activity
def log_agent_activity_streamlit(agent_type, message):
    st.session_state.agent_logs.append({
        "agent": agent_type,
        "message": message,
        "timestamp": datetime.now()
    })

# Connect log function to utils module
set_log_function(log_agent_activity_streamlit)

# Function to store project output artifacts
def store_output_artifact(agent_type, task_id, output_type, content):
    # If this project doesn't have outputs initialized yet
    if st.session_state.project_id not in st.session_state.project_outputs:
        st.session_state.project_outputs[st.session_state.project_id] = {}
        
    # If this agent doesn't have outputs initialized yet
    project_outputs = st.session_state.project_outputs[st.session_state.project_id]
    if agent_type not in project_outputs:
        project_outputs[agent_type] = {}
        
    # If this task doesn't have outputs initialized yet
    agent_outputs = project_outputs[agent_type]
    if task_id not in agent_outputs:
        agent_outputs[task_id] = {}
        
    # Store output by type
    task_outputs = agent_outputs[task_id]
    task_outputs[output_type] = content
    
    # Also store in database for persistence
    if st.session_state.orchestrator and st.session_state.orchestrator.db_connector:
        agent_id = "system"  # Default
        
        # Try to get actual agent ID
        agent = st.session_state.orchestrator.system_state.get_agent_by_type(agent_type)
        if agent:
            agent_id = agent.agent_id
            
        # Store in database
        st.session_state.orchestrator.db_connector.store_agent_output(
            task_id=task_id,
            agent_id=agent_id,
            output_type=output_type,
            content=content
        )
    
    # Return output ID for reference
    return f"{agent_type}_{task_id}_{output_type}"

# Function to process project requirements
def process_requirements(requirements):
    orchestrator = st.session_state.orchestrator
    
    # Create new project if needed
    if not st.session_state.project_id:
        with st.spinner("Creating new project..."):
            # Try to use Claude API first, with fallback to rule-based extraction
            if claude_client.is_available():
                log_agent_activity("system", "Using Claude to extract project name")
                project_name = claude_client.extract_project_name(requirements)
            else:
                log_agent_activity("system", "Claude API not available, using rule-based extraction")
                project_name = get_project_name_from_requirements(requirements)

            log_agent_activity("system", f"Extracted project name: {project_name}")
            
            # Store project name in session state for task execution
            st.session_state.project_name = project_name

            project_id = orchestrator.initialize_project(
                name=project_name.replace('_', ' ').title(),  # Convert to title case for display
                description=requirements[:200] if len(requirements) > 200 else requirements,
                requirements=requirements
            )
            st.session_state.project_id = project_id
            log_agent_activity("system", f"Created new project: {project_name}")

    # Process with Project Manager
    with st.spinner("Project Manager is analyzing requirements..."):
        agent = orchestrator.system_state.get_agent_by_type("project_manager")
        if agent:
            try:
                # Parse requirements
                log_agent_activity("project_manager", "Parsing requirements...")
                parsed_requirements = agent.agent_instance.parse_requirements(requirements)
                
                # Create task breakdown
                log_agent_activity("project_manager", "Creating task breakdown...")
                tasks = agent.agent_instance.create_task_breakdown(parsed_requirements)
                
                # Assign tasks to agents
                log_agent_activity("project_manager", "Assigning tasks to agents...")
                assigned_tasks = agent.agent_instance.assign_tasks_to_agents(tasks)
                
                # Store tasks in database and session state
                for task in assigned_tasks:
                    # Create task in database
                    task_id = orchestrator.db_connector.create_task(
                        project_id=st.session_state.project_id,
                        title=task.get("title", "Untitled Task"),
                        description=task.get("description", ""),
                        assigned_agent=task.get("assigned_agent", "developer")
                    )
                    
                    # Update task with ID
                    task["id"] = task_id
                    
                    # Add to session state
                    st.session_state.tasks.append(task)
                    
                    # Log task creation
                    log_agent_activity("project_manager", f"Created task: {task['title']} (assigned to {task['assigned_agent']})")
                    
                    # Send task to assigned agent via message bus
                    target_agent = orchestrator.system_state.get_agent_by_type(task.get("assigned_agent", "developer"))
                    if target_agent:
                        orchestrator.message_bus.send_message(Message(
                            sender_id=agent.agent_id,
                            receiver_id=target_agent.agent_id,
                            content=task,
                            message_type="task",
                            task_id=task_id,
                            project_id=st.session_state.project_id
                        ))
                
                log_agent_activity("project_manager", f"Created {len(assigned_tasks)} tasks")
                return True
                
            except Exception as e:
                log_agent_activity("project_manager", f"Error: {str(e)}")
                traceback.print_exc()
                return False
        else:
            log_agent_activity("system", "Project Manager agent not found")
            return False

# Main app layout
st.title("🚀 AI Development Team")
st.markdown("""
This system uses a team of specialized AI agents to build software projects based on your requirements.
Enter your project specifications below to get started.
""")

# Create sidebar
create_sidebar()

# Project requirements input
with st.container():
    requirements = st.text_area(
        "Project Requirements",
        value=st.session_state.requirements,
        height=200,
        placeholder="Enter your project requirements here. Describe what you want to build in detail."
    )
    
    # Save requirements in session state
    if requirements != st.session_state.requirements:
        st.session_state.requirements = requirements
    
    # Process button
    if st.button("Process Requirements"):
        if requirements:
            with st.spinner("Processing requirements..."):
                if process_requirements(requirements):
                    st.success("Requirements processed successfully!")
                else:
                    st.error("Error processing requirements")
        else:
            st.warning("Please enter project requirements")

# Display tasks
render_task_list()

# Display agent logs
render_agent_logs()

# Display project output
render_project_output()