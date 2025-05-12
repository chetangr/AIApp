import os
import sys
import argparse
import streamlit as st
from core.database import DatabaseConnector
from core.orchestration_simple import SimpleOrchestrator

# Need to initialize session state before importing app functions
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []

if "project_id" not in st.session_state:
    st.session_state.project_id = None

# Now import the functions from app
from app import run_task, log_agent_activity

def main():
    parser = argparse.ArgumentParser(description='Create and process a project using the multi-agent system')
    parser.add_argument('--name', type=str, required=True, help='Project name')
    parser.add_argument('--description', type=str, help='Project description')
    parser.add_argument('--requirements', type=str, required=True, help='Project requirements')
    parser.add_argument('--run-tasks', action='store_true', help='Run tasks after project creation')
    
    args = parser.parse_args()
    
    print(f"Creating project '{args.name}'...")
    
    # Create database connector
    db_connector = DatabaseConnector()
    
    # Create orchestrator
    orchestrator = SimpleOrchestrator(db_connector=db_connector)
    st.session_state.orchestrator = orchestrator

    # Initialize project
    project_id = orchestrator.initialize_project(
        name=args.name,
        description=args.description or args.name,
        requirements=args.requirements
    )

    # Store project ID in session state
    st.session_state.project_id = project_id

    print(f"Project created with ID: {project_id}")
    
    # Run the orchestration
    print("Running initial orchestration...")
    state = orchestrator.run(steps=3)
    
    # Get tasks
    tasks = orchestrator.db_connector.get_tasks_by_project(project_id)

    # Store tasks in session state
    st.session_state.tasks = tasks

    print(f"Created {len(tasks)} tasks:")
    for task in tasks:
        print(f" - {task['title']} (assigned to {task['assigned_agent']})")
    
    # Run tasks if requested
    if args.run_tasks and tasks:
        print("\nRunning tasks...")
        for task in tasks:
            print(f"Running task: {task['title']}")
            result = run_task(task['id'])
            if result:
                print(f" - Completed successfully")
            else:
                print(f" - Failed")
    
    print("\nProject creation complete!")
    print(f"Project directory: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projects')}")

if __name__ == "__main__":
    main()