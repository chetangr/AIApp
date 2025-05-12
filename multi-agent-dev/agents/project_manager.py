import datetime
from typing import Dict, List, Any

class ProjectManagerAgent:
    def __init__(self, db_connector=None):
        self.db_connector = db_connector
        self.system_prompt = """
        You are an expert Project Manager agent responsible for analyzing requirements, 
        breaking them into manageable tasks, and coordinating work among specialized development agents.
        You must ensure that all aspects of the project are properly addressed, tasks are clearly defined,
        and progress is tracked effectively. Your goal is to maximize efficiency and quality by
        optimizing task distribution and resolving bottlenecks.
        """

    def parse_requirements(self, requirements: str) -> Dict[str, Any]:
        """
        Parse natural language requirements into structured components.

        Args:
            requirements: Raw project requirements as text

        Returns:
            Dictionary containing parsed requirements with categorized components
        """
        # Convert to string if it's not already (handle dictionary or other inputs)
        if not isinstance(requirements, str):
            try:
                requirements = str(requirements)
            except:
                requirements = "Default project requirements"

        # Simple parsing logic - extract keywords and categorize
        components = []
        features = []
        technologies = []
        constraints = []

        # Look for component keywords
        component_keywords = ["database", "frontend", "backend", "ui", "api", "authentication", "storage"]
        for keyword in component_keywords:
            if keyword.lower() in requirements.lower():
                components.append(keyword)

        # Look for feature keywords
        feature_keywords = ["login", "signup", "search", "dashboard", "analytics", "profile", "settings"]
        for keyword in feature_keywords:
            if keyword.lower() in requirements.lower():
                features.append(keyword)

        # Look for technology keywords
        tech_keywords = ["python", "javascript", "react", "node", "sql", "nosql", "rest", "graphql"]
        for keyword in tech_keywords:
            if keyword.lower() in requirements.lower():
                technologies.append(keyword)

        # Create project name if possible
        project_name = "New Project"
        if len(requirements) > 10:
            # Use first sentence or first 40 chars as name
            end_idx = min(requirements.find('.'), 40)
            if end_idx < 0:
                end_idx = min(len(requirements), 40)
            project_name = requirements[:end_idx].strip()

        # Create parsed requirements
        parsed_requirements = {
            "project_name": project_name,
            "project_description": requirements[:200] if len(requirements) > 200 else requirements,
            "components": components or ["frontend", "backend", "database"],  # Default components
            "features": features or ["core functionality"],  # Default features
            "technologies": technologies or ["python"],  # Default technologies
            "constraints": constraints
        }

        return parsed_requirements
    
    def create_task_breakdown(self, parsed_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Break down requirements into specific, assignable tasks.

        Args:
            parsed_requirements: Structured requirements from parse_requirements

        Returns:
            List of task dictionaries with titles, descriptions, and dependencies
        """
        tasks = []

        # Extract information from parsed requirements
        components = parsed_requirements.get("components", [])
        features = parsed_requirements.get("features", [])
        technologies = parsed_requirements.get("technologies", [])
        project_description = parsed_requirements.get("project_description", "")

        # Generate tasks based on components
        for i, component in enumerate(components):
            task_id = f"component-{i+1}"

            if component.lower() == "frontend" or component.lower() == "ui":
                tasks.append({
                    "id": task_id,
                    "title": f"Design and implement {component} interface",
                    "description": f"Create the user interface for the {component} component based on the requirements. Ensure it is responsive and user-friendly.",
                    "dependencies": [],
                    "estimated_effort": "medium",
                    "component": component
                })
            elif component.lower() == "backend" or component.lower() == "api":
                tasks.append({
                    "id": task_id,
                    "title": f"Develop {component} services",
                    "description": f"Implement the {component} services including business logic and API endpoints as specified in requirements.",
                    "dependencies": [],
                    "estimated_effort": "high",
                    "component": component
                })
            elif component.lower() == "database":
                tasks.append({
                    "id": task_id,
                    "title": f"Design and implement {component} schema",
                    "description": f"Design the database schema and implement data models. Create necessary tables, indexes, and relationships.",
                    "dependencies": [],
                    "estimated_effort": "medium",
                    "component": component
                })
            else:
                tasks.append({
                    "id": task_id,
                    "title": f"Implement {component} component",
                    "description": f"Develop the {component} component according to the project requirements.",
                    "dependencies": [],
                    "estimated_effort": "medium",
                    "component": component
                })

        # Generate tasks based on features
        for i, feature in enumerate(features):
            task_id = f"feature-{i+1}"
            tasks.append({
                "id": task_id,
                "title": f"Implement {feature} feature",
                "description": f"Develop the {feature} feature including UI, backend logic, and database integration as needed.",
                "dependencies": [],
                "estimated_effort": "medium",
                "feature": feature
            })

        # Add testing tasks
        tasks.append({
            "id": "testing-1",
            "title": "Create test plan and test cases",
            "description": "Develop a comprehensive test plan and test cases covering all components and features.",
            "dependencies": [],
            "estimated_effort": "medium",
            "aspect": "testing"
        })

        # Add documentation task
        tasks.append({
            "id": "documentation-1",
            "title": "Create project documentation",
            "description": "Create comprehensive documentation for the project including setup instructions, user guide, and API documentation.",
            "dependencies": [],
            "estimated_effort": "medium",
            "aspect": "documentation"
        })

        # If no tasks were created, add default tasks
        if not tasks:
            tasks = [
                {
                    "id": "default-1",
                    "title": "Implement core functionality",
                    "description": f"Develop the main functionality of the project: {project_description}",
                    "dependencies": [],
                    "estimated_effort": "high"
                },
                {
                    "id": "default-2",
                    "title": "Create user interface",
                    "description": "Design and implement the user interface for the application.",
                    "dependencies": [],
                    "estimated_effort": "medium"
                },
                {
                    "id": "default-3",
                    "title": "Test application",
                    "description": "Create and execute test cases for the application.",
                    "dependencies": ["default-1", "default-2"],
                    "estimated_effort": "medium"
                },
                {
                    "id": "default-4",
                    "title": "Create documentation",
                    "description": "Create user and developer documentation for the application.",
                    "dependencies": ["default-1", "default-2"],
                    "estimated_effort": "low"
                }
            ]

        return tasks
    
    def assign_tasks_to_agents(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assign tasks to appropriate specialized agents based on task type.

        Args:
            tasks: List of tasks to be assigned

        Returns:
            Tasks with agent assignments added
        """
        assigned_tasks = []

        for task in tasks:
            # Determine which agent should handle this task

            # Check if the task has a specific aspect or component that helps identify the agent
            if "aspect" in task:
                if task["aspect"].lower() == "testing":
                    agent = "testing"
                elif task["aspect"].lower() == "documentation":
                    agent = "documentation"
                else:
                    agent = "developer"
            elif "component" in task:
                component = task["component"].lower()
                if component in ["frontend", "ui", "interface"]:
                    agent = "ui_ux"
                elif component in ["integration", "api", "connection"]:
                    agent = "integration"
                elif component in ["backend", "database", "server"]:
                    agent = "developer"
                else:
                    agent = "developer"
            else:
                # Use title and description to determine the best agent
                task_type = self._determine_task_type(task)
                agent = task_type

            # Add assignment and status to the task
            task["assigned_agent"] = agent
            task["status"] = "assigned"
            task["created_at"] = datetime.datetime.now()
            task["updated_at"] = datetime.datetime.now()

            assigned_tasks.append(task)

        return assigned_tasks
    
    def monitor_progress(self, project_id: str) -> Dict[str, Any]:
        """
        Track task completion and overall project progress.
        
        Args:
            project_id: ID of the project to monitor
            
        Returns:
            Project status summary with completion metrics
        """
        if not self.db_connector:
            return {"error": "Database connector not available"}
        
        tasks = self.db_connector.get_tasks_by_project(project_id)
        
        # Calculate progress metrics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task["status"] == "completed")
        in_progress_tasks = sum(1 for task in tasks if task["status"] == "in_progress")
        
        progress = {
            "project_id": project_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "status_counts": {status: sum(1 for task in tasks if task["status"] == status) 
                              for status in ["assigned", "in_progress", "completed", "blocked"]}
        }
        
        return progress
    
    def _determine_task_type(self, task: Dict[str, Any]) -> str:
        """
        Determine the type of a task based on its description and title.

        Args:
            task: Task dictionary

        Returns:
            Agent type that should handle the task
        """
        description = task.get("description", "").lower()
        title = task.get("title", "").lower()

        # Map task characteristics to agent types
        if any(term in description or term in title for term in ["ui", "interface", "design", "layout", "front", "user experience"]):
            return "ui_ux"
        elif any(term in description or term in title for term in ["test", "verify", "validate", "quality"]):
            return "testing"
        elif any(term in description or term in title for term in ["document", "manual", "guide", "help", "tutorial"]):
            return "documentation"
        elif any(term in description or term in title for term in ["connect", "integrate", "api", "service", "microservice"]):
            return "integration"
        else:
            return "developer"