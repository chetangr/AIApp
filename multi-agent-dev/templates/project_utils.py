import os
import re
from typing import Dict, Any, List, Optional

# Import required utilities
import sys
import streamlit as st
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Define local log function for testing
def log_agent_activity(agent_type, message):
    """Log agent activity"""
    print(f"[{agent_type}] {message}")

def get_app_name_from_task(task):
    """Extract an app name from the task description/title"""
    if "title" in task:
        # Clean the task title to use as app name
        app_name = task["title"].lower()
        # Remove any non-alphanumeric characters except spaces
        import re
        app_name = re.sub(r'[^\w\s]', '', app_name)
        # Replace spaces with underscores
        app_name = app_name.replace(' ', '_')
        return app_name
    return "app"  # Default fallback

def get_project_type(task):
    """Determine what type of project to create based on task details"""
    title = task.get("title", "").lower()
    description = task.get("description", "").lower()
    content = title + " " + description

    project_type = "generic"

    # Check for mobile apps
    if "android" in content or "mobile" in content:
        if "flutter" in content:
            project_type = "flutter"
        elif "react native" in content:
            project_type = "react_native"
        elif "android" in content:
            project_type = "android"
        elif "ios" in content or "iphone" in content or "apple" in content:
            project_type = "ios"
        else:
            project_type = "flutter"  # Default to Flutter for mobile

    # Check for web apps
    elif "web" in content:
        if "react" in content:
            project_type = "react"
        elif "angular" in content:
            project_type = "angular"
        elif "vue" in content:
            project_type = "vue"
        else:
            project_type = "react"  # Default to React for web

    # Check for backend/server
    elif "api" in content or "server" in content or "backend" in content:
        if "python" in content or "django" in content or "flask" in content:
            project_type = "python_backend"
        elif "node" in content or "express" in content:
            project_type = "node_backend"
        else:
            project_type = "python_backend"  # Default to Python for backend

    return project_type

def get_project_dir():
    """Get the project directory from session state, ensuring a consistent location for all tasks
    
    Returns:
        The absolute path to the project directory
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Get the project name from session state
    project_name = None
    if "project_name" in st.session_state and st.session_state.project_name:
        project_name = st.session_state.project_name
    else:
        # Try to derive the project name from the project_id in orchestrator
        try:
            if st.session_state.orchestrator and st.session_state.orchestrator.system_state:
                project_id = st.session_state.orchestrator.system_state.project_id
                projects = st.session_state.orchestrator.db_connector.get_all_projects()
                for project in projects:
                    if project["id"] == project_id:
                        # Found the project
                        project_name = project["name"].lower().replace(" ", "_")
                        # Cache it for future use
                        st.session_state.project_name = project_name
                        break
        except Exception as e:
            print(f"Error extracting project name: {str(e)}")
    
    # If we still don't have a name, use a generic one
    if not project_name:
        project_name = "app"
    
    # Create the project directory
    project_dir = os.path.join(base_dir, "projects", project_name.capitalize())
    os.makedirs(project_dir, exist_ok=True)
    
    return project_dir

def create_app_from_task(task, agent_type):
    """Create a project based on the task details"""
    # Get the project directory - this ensures consistency across all tasks
    project_dir = get_project_dir()
    
    # Get the project name from session state
    project_name = None
    if "project_name" in st.session_state and st.session_state.project_name:
        project_name = st.session_state.project_name
    else:
        # Fallback to a suitable name based on the project dir
        project_name = os.path.basename(project_dir).lower()
    
    # Get the project type from task
    project_type = get_project_type(task)
    
    log_agent_activity(agent_type, f"Creating {project_type} project in {project_dir}")
    
    # Create the appropriate type of project
    success = False
    
    if project_type == "flutter":
        from templates.flutter_app import create_flutter_app
        success = create_flutter_app(task, project_name, project_dir)
    elif project_type in ["react", "web"]:
        from templates.react_app import create_react_app
        success = create_react_app(task, project_name, project_dir)
    else:
        # For other project types, create a basic structure
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        
        # Create more appropriate directories for Python projects
        if project_type == "python_backend":
            # Create standard Python package structure
            package_name = project_name.replace("-", "_").lower()
            os.makedirs(os.path.join(project_dir, package_name), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
            
            # Create __init__.py
            with open(os.path.join(project_dir, package_name, "__init__.py"), "w") as f:
                f.write(f"""\"\"\"
{project_name.replace('_', ' ').title()} package.
\"\"\"

__version__ = "0.1.0"
""")
            
            # Create main.py
            with open(os.path.join(project_dir, package_name, "main.py"), "w") as f:
                f.write(f"""\"\"\"
Main module for {project_name.replace('_', ' ').title()}.
\"\"\"

def main():
    \"\"\"Run the main application.\"\"\"
    print("Starting {project_name.replace('_', ' ').title()}...")

if __name__ == "__main__":
    main()
""")
            
            # Create setup.py
            with open(os.path.join(project_dir, "setup.py"), "w") as f:
                f.write(f"""from setuptools import setup, find_packages

setup(
    name="{project_name.replace('_', '-')}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    entry_points={{
        'console_scripts': [
            '{project_name.replace("_", "-")}={package_name}.main:main',
        ],
    }},
)
""")
            
            # Create README.md
            with open(os.path.join(project_dir, "README.md"), "w") as f:
                f.write(f"""# {project_name.replace('_', ' ').title()}

{task.get('description', 'A Python backend application.')}

## Installation

```bash
pip install -e .
```

## Usage

```python
from {package_name} import main

main.main()
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```
""")
        else:
            # Generic README for other project types
            with open(os.path.join(project_dir, "README.md"), "w") as f:
                f.write(f"# {project_name.replace('_', ' ').title()}\n\n{task.get('description', '')}")
        
        success = True
    
    return {
        "success": success,
        "app_name": project_name,
        "project_type": project_type,
        "project_dir": project_dir
    }