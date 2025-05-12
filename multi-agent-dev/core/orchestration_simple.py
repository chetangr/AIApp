import datetime
import uuid
import traceback
import sys
import os.path
import json
from typing import Dict, Any, List, Optional, Union, Tuple

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import datetime-safe serialization functions
from utils import serialize_state, deserialize_state

from core.database import DatabaseConnector
from core.messaging import MessageBus, Message

# Import agents
from agents.project_manager import ProjectManagerAgent
from agents.developer import DeveloperAgent
from agents.ui_ux import UIUXAgent
from agents.integration import IntegrationAgent
from agents.testing import TestingAgent
from agents.documentation import DocumentationAgent
from agents.error_handling import ErrorHandlingAgent

class AgentState:
    """
    Class representing the state of an agent in the system.
    """
    def __init__(self, agent_id: str, agent_type: str, agent_instance: Any):
        """
        Initialize agent state.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (e.g., "project_manager", "developer")
            agent_instance: Instance of the agent class
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.agent_instance = agent_instance
        self.status = "idle"  # idle, working, blocked, error
        self.current_task_id = None
        self.task_history: List[str] = []
        self.error = None
        self.last_active = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert agent state to dictionary with serializable values.
        
        Returns:
            Dictionary representation of agent state
        """
        # Create basic dictionary with primitive values
        result = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "current_task_id": self.current_task_id,
            "task_history": self.task_history,
            "error": self.error
        }
        
        # Handle datetime separately to ensure it's serializable
        try:
            # Convert datetime to ISO format string
            result["last_active"] = self.last_active.isoformat()
        except:
            # Use a string fallback if conversion fails
            result["last_active"] = str(self.last_active)
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], agent_instance: Any) -> 'AgentState':
        """
        Create agent state from dictionary.
        
        Args:
            data: Dictionary representation of agent state
            agent_instance: Instance of the agent class
            
        Returns:
            Agent state instance
        """
        state = cls(
            agent_id=data.get("agent_id"),
            agent_type=data.get("agent_type"),
            agent_instance=agent_instance
        )
        state.status = data.get("status", "idle")
        state.current_task_id = data.get("current_task_id")
        state.task_history = data.get("task_history", [])
        state.error = data.get("error")
        
        # Parse last_active if it's a string
        last_active = data.get("last_active")
        if isinstance(last_active, str):
            try:
                state.last_active = datetime.datetime.fromisoformat(last_active)
            except ValueError:
                state.last_active = datetime.datetime.now()
        else:
            state.last_active = last_active or datetime.datetime.now()
        
        return state


class SystemState:
    """
    Class representing the overall state of the multi-agent system.
    """
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize system state.
        
        Args:
            project_id: Optional project ID
        """
        self.project_id = project_id
        self.agents: Dict[str, AgentState] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Message] = []
        self.errors: List[Dict[str, Any]] = []
        self.status = "initializing"  # initializing, running, paused, completed, error
        self.current_phase = "setup"
        self.started_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.checkpoint_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert system state to dictionary with serializable values.
        
        Returns:
            Dictionary representation of system state
        """
        # Convert all components to serializable values
        try:
            agents_dict = {}
            for agent_id, state in self.agents.items():
                agents_dict[agent_id] = state.to_dict()
                
            messages_list = []
            for message in self.messages:
                try:
                    messages_list.append(message.to_dict())
                except Exception as e:
                    # If message conversion fails, use a simplified representation
                    messages_list.append({
                        "id": message.id,
                        "error": f"Could not convert message: {str(e)}"
                    })
                    
            result = {
                "project_id": self.project_id,
                "agents": agents_dict,
                "tasks": self.tasks,
                "messages": messages_list,
                "errors": self.errors,
                "status": self.status,
                "current_phase": self.current_phase,
                "checkpoint_id": self.checkpoint_id
            }
            
            # Convert datetime objects to strings
            result["started_at"] = self.started_at.isoformat()
            result["updated_at"] = self.updated_at.isoformat()
            
            return result
        except Exception as e:
            # If conversion fails, return a simplified state
            print(f"Error converting system state to dict: {str(e)}")
            return {
                "project_id": self.project_id,
                "status": self.status,
                "error": f"Could not convert full state: {str(e)}"
            }
    
    def get_agent_by_type(self, agent_type: str) -> Optional[AgentState]:
        """
        Get agent state by agent type.
        
        Args:
            agent_type: Type of agent to find
            
        Returns:
            Agent state or None if not found
        """
        for agent_state in self.agents.values():
            if agent_state.agent_type == agent_type:
                return agent_state
        return None
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        Update agent status.
        
        Args:
            agent_id: Agent ID
            status: New status
            
        Returns:
            True if agent was found and updated, False otherwise
        """
        if agent_id in self.agents:
            self.agents[agent_id].status = status
            self.agents[agent_id].last_active = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
            return True
        return False
    
    def assign_task_to_agent(self, agent_id: str, task_id: str) -> bool:
        """
        Assign a task to an agent.
        
        Args:
            agent_id: Agent ID
            task_id: Task ID
            
        Returns:
            True if agent was found and task assigned, False otherwise
        """
        if agent_id in self.agents:
            self.agents[agent_id].current_task_id = task_id
            self.agents[agent_id].task_history.append(task_id)
            self.agents[agent_id].status = "working"
            self.agents[agent_id].last_active = datetime.datetime.now()
            self.updated_at = datetime.datetime.now()
            return True
        return False
    
    def add_error(self, error: Dict[str, Any]) -> None:
        """
        Add an error to the system state.
        
        Args:
            error: Error details
        """
        # Ensure all datetime objects are serialized
        try:
            # Attempt to serialize to catch any issues
            json_error = json.loads(serialize_state(error))
            self.errors.append(json_error)
        except Exception as e:
            # If serialization fails, use a simpler error
            print(f"Error serializing error data: {str(e)}")
            self.errors.append({
                "error_type": error.get("error_type", "Unknown"),
                "error_message": error.get("error_message", str(e)),
                "created_at": datetime.datetime.now().isoformat()
            })
            
        self.updated_at = datetime.datetime.now()
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the system state.
        
        Args:
            message: Message to add
        """
        self.messages.append(message)
        self.updated_at = datetime.datetime.now()


class SimpleOrchestrator:
    """
    Simple orchestration without using LangGraph for the multi-agent system.
    """
    def __init__(self, db_connector: Optional[DatabaseConnector] = None,
                 llm_service: Any = None):
        """
        Initialize the orchestrator.

        Args:
            db_connector: Database connector for persistence
            llm_service: LLM service for agent interactions
        """
        self.db_connector = db_connector or DatabaseConnector()
        self.llm_service = llm_service  # In a real implementation, this would be a specific LLM service
        self.message_bus = MessageBus(db_connector=self.db_connector)
        self.system_state = SystemState()

        # Create agent instances
        self._create_agent_instances()

    def reset(self, project_id: Optional[str] = None):
        """
        Reset the orchestrator to a clean state.

        Args:
            project_id: Optional project ID to initialize with
        """
        # Recreate the message bus
        self.message_bus = MessageBus(db_connector=self.db_connector)

        # Initialize system state
        if project_id:
            self.system_state = SystemState(project_id=project_id)

            # Check if project exists
            project = self.db_connector.get_project(project_id)
            if not project:
                print(f"Warning: Project {project_id} not found")
                self.system_state = SystemState()
        else:
            self.system_state = SystemState()

        # Create agent instances
        self._create_agent_instances()

        return self
    
    def _create_agent_instances(self) -> Dict[str, Any]:
        """
        Create instances of all agents.
        
        Returns:
            Dictionary mapping agent types to instances
        """
        agents = {
            "project_manager": ProjectManagerAgent(db_connector=self.db_connector),
            "developer": DeveloperAgent(db_connector=self.db_connector),
            "ui_ux": UIUXAgent(db_connector=self.db_connector),
            "integration": IntegrationAgent(db_connector=self.db_connector),
            "testing": TestingAgent(db_connector=self.db_connector),
            "documentation": DocumentationAgent(db_connector=self.db_connector),
            "error_handling": ErrorHandlingAgent(db_connector=self.db_connector, orchestrator=self)
        }
        
        # Initialize agent states
        for agent_type, agent_instance in agents.items():
            agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
            agent_state = AgentState(agent_id, agent_type, agent_instance)
            self.system_state.agents[agent_id] = agent_state
        
        return agents
    
    def _process_agent_messages(self, agent_type: str) -> Dict[str, Any]:
        """
        Process messages for a specific agent type.
        
        Args:
            agent_type: Type of agent to process messages for
            
        Returns:
            Updated state information
        """
        # Get agent state
        agent_state = self.system_state.get_agent_by_type(agent_type)
        if not agent_state:
            return {"error": f"Agent of type {agent_type} not found"}
        
        # Mark agent as working
        self.system_state.update_agent_status(agent_state.agent_id, "working")
        
        # Get unread messages
        messages = self.message_bus.get_unread_messages(agent_state.agent_id)
        if not messages:
            # No messages, mark as idle
            self.system_state.update_agent_status(agent_state.agent_id, "idle")
            return {"status": "idle", "message": "No messages to process"}
        
        # Simplified state to return
        state = {
            "tasks": [],
            "implementations": [],
            "ui_implementations": [],
            "integrated_systems": [],
            "test_reports": [],
            "documentation": [],
            "error_handling_results": [],
            "next": "project_manager",  # Default next agent
            "agent_processed": agent_type
        }
        
        # Process messages based on agent type
        try:
            # Just log received messages for now
            print(f"Processing {len(messages)} messages for {agent_type} agent")
            
            # For project manager, process requirements and create tasks
            if agent_type == "project_manager":
                for message in messages:
                    if message.message_type == "requirements":
                        print(f"Project manager processing requirements: {message.id}")

                        try:
                            # Actually process requirements and create tasks
                            requirements = message.content
                            print(f"Requirements content: {requirements}")

                            # Parse requirements using agent
                            parsed_requirements = agent_state.agent_instance.parse_requirements(requirements)

                            # Create task breakdown
                            tasks = agent_state.agent_instance.create_task_breakdown(parsed_requirements)

                            # Assign tasks to agents
                            assigned_tasks = agent_state.agent_instance.assign_tasks_to_agents(tasks)

                            # Store tasks in the database
                            for task in assigned_tasks:
                                # Create friendly task title if missing
                                if not task.get("title"):
                                    task["title"] = f"Task {len(assigned_tasks)}"

                                # Create task in database
                                task_id = self.db_connector.create_task(
                                    project_id=self.system_state.project_id,
                                    title=task.get("title", "Untitled Task"),
                                    description=task.get("description", ""),
                                    assigned_agent=task.get("assigned_agent", "developer")
                                )

                                # Update task with ID
                                task["id"] = task_id

                                # Assign the task to the agent
                                target_agent = self.system_state.get_agent_by_type(task.get("assigned_agent", "developer"))
                                if target_agent:
                                    self.system_state.assign_task_to_agent(target_agent.agent_id, task_id)

                                    # Send task to the agent
                                    self.message_bus.send_message(Message(
                                        sender_id=agent_state.agent_id,
                                        receiver_id=target_agent.agent_id,
                                        content=task,
                                        message_type="task",
                                        task_id=task_id,
                                        project_id=self.system_state.project_id
                                    ))

                            # Add created tasks to state
                            state["tasks"] = assigned_tasks
                            print(f"Created {len(assigned_tasks)} tasks")

                        except Exception as e:
                            print(f"Error processing requirements: {str(e)}")
                            traceback.print_exc()

                            # Create a fallback task for demonstration
                            task_id = self.db_connector.create_task(
                                project_id=self.system_state.project_id,
                                title="Sample Development Task",
                                description="This is a sample task created when processing requirements",
                                assigned_agent="developer"
                            )

                            # Create a basic task dictionary
                            task = {
                                "id": task_id,
                                "title": "Sample Development Task",
                                "description": "This is a sample task created when processing requirements",
                                "assigned_agent": "developer"
                            }

                            # Assign to developer agent
                            developer_agent = self.system_state.get_agent_by_type("developer")
                            if developer_agent:
                                self.system_state.assign_task_to_agent(developer_agent.agent_id, task_id)

                                # Send task to developer
                                self.message_bus.send_message(Message(
                                    sender_id=agent_state.agent_id,
                                    receiver_id=developer_agent.agent_id,
                                    content=task,
                                    message_type="task",
                                    task_id=task_id,
                                    project_id=self.system_state.project_id
                                ))

                            # Add task to state
                            state["tasks"] = [task]

                        # Mark message as handled
                        self.message_bus.mark_processed(message.id)

                        # Update state to indicate project manager was processed
                        state["next"] = "developer"
            
            # Mark all messages as processed
            for message in messages:
                self.message_bus.mark_processed(message.id)
                
            # Mark agent as idle
            self.system_state.update_agent_status(agent_state.agent_id, "idle")
            
            return state
        except Exception as e:
            # Handle exception
            error_data = {
                "agent_id": agent_state.agent_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Add error to system state
            self.system_state.add_error(error_data)
            
            # Mark agent as error
            self.system_state.update_agent_status(agent_state.agent_id, "error")
            
            # Return error state
            return {
                "error": str(e),
                "next": "error_handling"  # Route to error handling
            }
    
    def initialize_project(self, name: str, description: str, requirements: str) -> str:
        """
        Initialize a new project.
        
        Args:
            name: Project name
            description: Project description
            requirements: Project requirements
            
        Returns:
            Project ID
        """
        # Check if this is for a new project or an existing one
        existing_project = None

        try:
            # Try to find the project by name first
            all_projects = self.db_connector.get_all_projects()
            existing_project = next((p for p in all_projects if p["name"] == name), None)
        except Exception as e:
            print(f"Error checking for existing project: {str(e)}")

        # Use existing project ID or create a new one
        if existing_project:
            print(f"Using existing project: {existing_project['id']}")
            project_id = existing_project["id"]
            # Update description if needed
            if description and description != existing_project["description"]:
                self.db_connector.update_project(project_id, {"description": description})
        else:
            # Create new project in database
            project_id = self.db_connector.create_project(name, description)
            print(f"Created new project: {project_id}")

        # Initialize system state with the project ID
        self.system_state = SystemState(project_id=project_id)
        
        # Create agent instances
        self._create_agent_instances()
        
        # Initial state
        initial_state = {
            "tasks": [],
            "implementations": [],
            "ui_implementations": [],
            "integrated_systems": [],
            "test_reports": [],
            "documentation": [],
            "error_handling_results": [],
            "next": "project_manager"
        }
        
        # Send requirements to project manager
        project_manager = self.system_state.get_agent_by_type("project_manager")
        if project_manager:
            print(f"Sending requirements to project manager: {project_manager.agent_id}")
            try:
                self.message_bus.send_message(Message(
                    sender_id="system",
                    receiver_id=project_manager.agent_id,
                    content=requirements,
                    message_type="requirements",
                    project_id=project_id
                ))
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                # Still continue since we can recover
        
        # Store initial checkpoint
        checkpoint_id = self.save_checkpoint(initial_state)
        self.system_state.checkpoint_id = checkpoint_id
        
        return project_id
    
    def run(self, steps: int = 1) -> Dict[str, Any]:
        """
        Run the orchestration for a specified number of steps.
        
        Args:
            steps: Number of steps to run
            
        Returns:
            Current system state
        """
        if not self.system_state.project_id:
            raise ValueError("Project not initialized")
        
        # Load the latest checkpoint
        current_state = self.load_checkpoint(self.system_state.checkpoint_id)
        
        # Update system status
        self.system_state.status = "running"
        
        # Simplified run process - just process messages for agents in sequence
        for _ in range(steps):
            try:
                # Determine which agent to process
                current_agent = current_state.get("next", "project_manager")
                print(f"Processing agent: {current_agent}")
                
                # Process messages for the agent
                next_state = self._process_agent_messages(current_agent)
                
                # Check if we hit an error
                if "error" in next_state:
                    print(f"Error processing agent {current_agent}: {next_state['error']}")
                    # Route to error handling if serious
                    if "next" in next_state and next_state["next"] == "error_handling":
                        current_state["next"] = "error_handling"
                    # Otherwise just continue
                else:
                    # Update current state
                    current_state.update(next_state)
                
                # Save checkpoint
                checkpoint_id = self.save_checkpoint(current_state)
                self.system_state.checkpoint_id = checkpoint_id
                
                # Update system state timestamp
                self.system_state.updated_at = datetime.datetime.now()
                
            except Exception as e:
                # Handle any errors
                print(f"Error in orchestration run: {str(e)}")
                error_data = {
                    "agent_id": "system",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stack_trace": traceback.format_exc(),
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                # Add to system state
                self.system_state.add_error(error_data)
                
                # Update system status
                self.system_state.status = "error"
                break
        
        # Return system state as a serializable dictionary
        try:
            state_dict = self.system_state.to_dict()
            # Ensure it's fully serializable with datetime handling
            serialized = serialize_state(state_dict)
            return json.loads(serialized)
        except Exception as e:
            # If serialization fails, return simplified state
            print(f"Error serializing system state: {str(e)}")
            return {
                "project_id": self.system_state.project_id,
                "status": self.system_state.status,
                "error": f"Error serializing state: {str(e)}"
            }
    
    def save_checkpoint(self, state: Dict[str, Any]) -> str:
        """
        Save a checkpoint of the current state.
        
        Args:
            state: Current state
            
        Returns:
            Checkpoint ID
        """
        try:
            # Store checkpoint in database
            checkpoint_id = self.db_connector.store_checkpoint(state)
            return checkpoint_id
        except Exception as e:
            print(f"Error saving checkpoint: {str(e)}")
            # Return a simple UUID as fallback
            return str(uuid.uuid4())
    
    def load_checkpoint(self, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint ID to load, or None for latest
            
        Returns:
            Checkpoint state
        """
        try:
            if checkpoint_id:
                # Load specific checkpoint
                checkpoint = self.db_connector.get_checkpoint(checkpoint_id)
                if checkpoint:
                    return checkpoint.get("checkpoint_data", {})
            
            # Load latest checkpoint
            checkpoint = self.db_connector.get_latest_checkpoint()
            if checkpoint:
                return checkpoint.get("checkpoint_data", {})
        except Exception as e:
            print(f"Error loading checkpoint: {str(e)}")
        
        # Return empty state if no checkpoint found
        return {
            "tasks": [],
            "implementations": [],
            "ui_implementations": [],
            "integrated_systems": [],
            "test_reports": [],
            "documentation": [],
            "error_handling_results": [],
            "next": "project_manager"
        }
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get the current status of a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project status
        """
        try:
            # Get project data
            project = self.db_connector.get_project(project_id)
            if not project:
                return {"error": "Project not found"}
            
            # Get tasks
            tasks = self.db_connector.get_tasks_by_project(project_id)
            
            # Get errors
            errors = []
            for task in tasks:
                task_errors = self.db_connector.get_errors_by_task(task["id"])
                errors.extend(task_errors)
            
            # Calculate progress metrics
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task["status"] == "completed")
            in_progress_tasks = sum(1 for task in tasks if task["status"] == "in_progress")
            blocked_tasks = sum(1 for task in tasks if task["status"] == "blocked")
            
            # Create status summary with serializable dates
            status = {
                "project": {
                    "id": project.get("id"),
                    "name": project.get("name"),
                    "description": project.get("description"),
                    "status": project.get("status"),
                    "created_at": project.get("created_at").isoformat() if isinstance(project.get("created_at"), datetime.datetime) else str(project.get("created_at")),
                    "updated_at": project.get("updated_at").isoformat() if isinstance(project.get("updated_at"), datetime.datetime) else str(project.get("updated_at"))
                },
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "in_progress": in_progress_tasks,
                    "blocked": blocked_tasks,
                    "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                },
                "errors": {
                    "total": len(errors),
                    "open": sum(1 for error in errors if error["status"] == "open"),
                    "resolved": sum(1 for error in errors if error["status"] == "resolved")
                },
                "agent_status": {},
                "system_status": self.system_state.status if project_id == self.system_state.project_id else "unknown"
            }
            
            # Add agent status with serializable dates
            if project_id == self.system_state.project_id:
                for agent_id, state in self.system_state.agents.items():
                    status["agent_status"][agent_id] = {
                        "type": state.agent_type,
                        "status": state.status,
                        "current_task": state.current_task_id,
                        "last_active": state.last_active.isoformat() if isinstance(state.last_active, datetime.datetime) else str(state.last_active)
                    }
            
            # Verify the status is fully serializable
            serialized = serialize_state(status)
            return json.loads(serialized)
        
        except Exception as e:
            # If there's an error, return a simplified status
            print(f"Error getting project status: {str(e)}")
            return {
                "project": {"id": project_id, "name": "Unknown"},
                "status": "error",
                "error": f"Error retrieving project status: {str(e)}"
            }