import os
import os.path
import datetime
import json
import uuid
import duckdb
import sys
from typing import Dict, Any, List, Optional, Union

# Import custom utility function for serialization with datetime support
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import serialize_state, deserialize_state

class DatabaseConnector:
    def __init__(self, db_path: str = None):
        """
        Initialize the DuckDB database connector.
        
        Args:
            db_path: Path to the DuckDB database file
        """
        if db_path is None:
            # Use default path in data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "multi_agent_dev.duckdb")
            
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Initialize the database schema if it doesn't exist."""
        
        # Create projects table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                status VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Create tasks table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id VARCHAR PRIMARY KEY,
                project_id VARCHAR,
                title VARCHAR NOT NULL,
                description TEXT,
                assigned_agent VARCHAR,
                status VARCHAR,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Create agent_outputs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id VARCHAR PRIMARY KEY,
                task_id VARCHAR,
                agent_id VARCHAR,
                output_type VARCHAR,
                content TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Create errors table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id VARCHAR PRIMARY KEY,
                task_id VARCHAR,
                agent_id VARCHAR,
                error_type VARCHAR,
                error_message TEXT,
                stack_trace TEXT,
                status VARCHAR,
                created_at TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        
        # Create system_checkpoints table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS system_checkpoints (
                id VARCHAR PRIMARY KEY,
                timestamp TIMESTAMP,
                checkpoint_data TEXT
            )
        """)
    
    def create_project(self, name: str, description: str = None) -> str:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            
        Returns:
            Project ID
        """
        project_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        self.conn.execute("""
            INSERT INTO projects (id, name, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, name, description, "created", now, now))
        
        return project_id
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project data
        """
        result = self.conn.execute("""
            SELECT * FROM projects WHERE id = ?
        """, (project_id,)).fetchone()
        
        if not result:
            return None
        
        # Convert result to dictionary
        columns = ["id", "name", "description", "status", "created_at", "updated_at"]
        return {columns[i]: result[i] for i in range(len(columns))}
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        Get all projects.
        
        Returns:
            List of project data
        """
        results = self.conn.execute("SELECT * FROM projects").fetchall()
        
        # Convert results to list of dictionaries
        columns = ["id", "name", "description", "status", "created_at", "updated_at"]
        return [{columns[i]: row[i] for i in range(len(columns))} for row in results]
    
    def update_project(self, project_id: str, data: Dict[str, Any]) -> bool:
        """
        Update project data.
        
        Args:
            project_id: Project ID
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        # Get current project data
        project = self.get_project(project_id)
        if not project:
            return False
        
        # Update fields
        updated_fields = {}
        for field in ["name", "description", "status"]:
            if field in data:
                updated_fields[field] = data[field]
        
        if not updated_fields:
            return True  # Nothing to update
        
        # Build SQL query
        set_clause = ", ".join(f"{field} = ?" for field in updated_fields.keys())
        set_values = list(updated_fields.values())
        
        # Add updated_at
        set_clause += ", updated_at = ?"
        set_values.append(datetime.datetime.now())
        
        # Add project_id
        set_values.append(project_id)
        
        # Execute update
        self.conn.execute(f"""
            UPDATE projects SET {set_clause} WHERE id = ?
        """, set_values)
        
        return True
    
    def create_task(self, project_id: str, title: str, description: str = None, 
                   assigned_agent: str = None) -> str:
        """
        Create a new task for a project.
        
        Args:
            project_id: Project ID
            title: Task title
            description: Task description
            assigned_agent: Agent assigned to the task
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        self.conn.execute("""
            INSERT INTO tasks (id, project_id, title, description, assigned_agent, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (task_id, project_id, title, description, assigned_agent, "created", now, now))
        
        return task_id
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task data
        """
        result = self.conn.execute("""
            SELECT * FROM tasks WHERE id = ?
        """, (task_id,)).fetchone()
        
        if not result:
            return None
        
        # Convert result to dictionary
        columns = ["id", "project_id", "title", "description", "assigned_agent", "status", 
                  "created_at", "updated_at"]
        return {columns[i]: result[i] for i in range(len(columns))}
    
    def get_tasks_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of task data
        """
        results = self.conn.execute("""
            SELECT * FROM tasks WHERE project_id = ?
        """, (project_id,)).fetchall()
        
        # Convert results to list of dictionaries
        columns = ["id", "project_id", "title", "description", "assigned_agent", "status", 
                  "created_at", "updated_at"]
        return [{columns[i]: row[i] for i in range(len(columns))} for row in results]
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> bool:
        """
        Update task data.
        
        Args:
            task_id: Task ID
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        # Get current task data
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Update fields
        updated_fields = {}
        for field in ["title", "description", "assigned_agent", "status"]:
            if field in data:
                updated_fields[field] = data[field]
        
        if not updated_fields:
            return True  # Nothing to update
        
        # Build SQL query
        set_clause = ", ".join(f"{field} = ?" for field in updated_fields.keys())
        set_values = list(updated_fields.values())
        
        # Add updated_at
        set_clause += ", updated_at = ?"
        set_values.append(datetime.datetime.now())
        
        # Add task_id
        set_values.append(task_id)
        
        # Execute update
        self.conn.execute(f"""
            UPDATE tasks SET {set_clause} WHERE id = ?
        """, set_values)
        
        return True
    
    def store_agent_output(self, task_id: str, agent_id: str, output_type: str, 
                          content: Union[str, Dict, List]) -> str:
        """
        Store agent output for a task.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            output_type: Type of output
            content: Output content
            
        Returns:
            Output ID
        """
        output_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        # Always convert content to JSON string using safe serialization
        # First convert to string if it's not already
        if not isinstance(content, str):
            try:
                content = serialize_state(content)
            except Exception as e:
                # If serialization fails, use a simplified error message
                print(f"Error serializing content: {str(e)}")
                content = json.dumps({"error": f"Could not serialize content: {str(e)}"})
        
        self.conn.execute("""
            INSERT INTO agent_outputs (id, task_id, agent_id, output_type, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (output_id, task_id, agent_id, output_type, content, now))
        
        return output_id
    
    def get_agent_outputs(self, task_id: str, agent_id: str = None) -> List[Dict[str, Any]]:
        """
        Get agent outputs for a task.
        
        Args:
            task_id: Task ID
            agent_id: Optional agent ID to filter
            
        Returns:
            List of output data
        """
        if agent_id:
            results = self.conn.execute("""
                SELECT * FROM agent_outputs WHERE task_id = ? AND agent_id = ?
                ORDER BY created_at DESC
            """, (task_id, agent_id)).fetchall()
        else:
            results = self.conn.execute("""
                SELECT * FROM agent_outputs WHERE task_id = ?
                ORDER BY created_at DESC
            """, (task_id,)).fetchall()
        
        # Convert results to list of dictionaries
        columns = ["id", "task_id", "agent_id", "output_type", "content", "created_at"]
        outputs = [{columns[i]: row[i] for i in range(len(columns))} for row in results]
        
        # Parse JSON content
        for output in outputs:
            try:
                output["content"] = json.loads(output["content"])
            except (json.JSONDecodeError, TypeError):
                # Keep as is if not valid JSON
                pass
        
        return outputs
    
    def store_error(self, task_id: str, agent_id: str, error_type: str, error_message: str,
                   stack_trace: str = None) -> str:
        """
        Store an error.
        
        Args:
            task_id: Task ID
            agent_id: Agent ID
            error_type: Type of error
            error_message: Error message
            stack_trace: Stack trace
            
        Returns:
            Error ID
        """
        error_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        self.conn.execute("""
            INSERT INTO errors (id, task_id, agent_id, error_type, error_message, stack_trace, 
                              status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (error_id, task_id, agent_id, error_type, error_message, stack_trace, "open", now))
        
        return error_id
    
    def get_error(self, error_id: str) -> Dict[str, Any]:
        """
        Get error by ID.
        
        Args:
            error_id: Error ID
            
        Returns:
            Error data
        """
        result = self.conn.execute("""
            SELECT * FROM errors WHERE id = ?
        """, (error_id,)).fetchone()
        
        if not result:
            return None
        
        # Convert result to dictionary
        columns = ["id", "task_id", "agent_id", "error_type", "error_message", "stack_trace",
                  "status", "created_at", "resolved_at", "resolution"]
        return {columns[i]: result[i] for i in range(len(columns))}
    
    def get_errors_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all errors for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of error data
        """
        results = self.conn.execute("""
            SELECT * FROM errors WHERE task_id = ?
            ORDER BY created_at DESC
        """, (task_id,)).fetchall()
        
        # Convert results to list of dictionaries
        columns = ["id", "task_id", "agent_id", "error_type", "error_message", "stack_trace",
                  "status", "created_at", "resolved_at", "resolution"]
        return [{columns[i]: row[i] for i in range(len(columns))} for row in results]
    
    def get_all_errors(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get all errors, optionally filtered by status.
        
        Args:
            status: Optional status to filter
            
        Returns:
            List of error data
        """
        if status:
            results = self.conn.execute("""
                SELECT * FROM errors WHERE status = ?
                ORDER BY created_at DESC
            """, (status,)).fetchall()
        else:
            results = self.conn.execute("""
                SELECT * FROM errors
                ORDER BY created_at DESC
            """).fetchall()
        
        # Convert results to list of dictionaries
        columns = ["id", "task_id", "agent_id", "error_type", "error_message", "stack_trace",
                  "status", "created_at", "resolved_at", "resolution"]
        return [{columns[i]: row[i] for i in range(len(columns))} for row in results]
    
    def update_error_status(self, error_id: str, status: str, resolution: str = None,
                           resolved_at: datetime.datetime = None) -> bool:
        """
        Update error status.
        
        Args:
            error_id: Error ID
            status: New status
            resolution: Resolution description
            resolved_at: Resolution timestamp
            
        Returns:
            True if successful, False otherwise
        """
        # Get current error data
        error = self.get_error(error_id)
        if not error:
            return False
        
        # Use current time if not provided
        if resolved_at is None and status == "resolved":
            resolved_at = datetime.datetime.now()
        
        # Build SQL query
        if status == "resolved":
            self.conn.execute("""
                UPDATE errors SET status = ?, resolution = ?, resolved_at = ?
                WHERE id = ?
            """, (status, resolution, resolved_at, error_id))
        else:
            self.conn.execute("""
                UPDATE errors SET status = ?
                WHERE id = ?
            """, (status, error_id))
        
        return True
    
    def store_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """
        Store a system checkpoint.
        
        Args:
            checkpoint_data: Checkpoint data
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = str(uuid.uuid4())
        now = datetime.datetime.now()
        
        # Convert checkpoint data to JSON string with datetime handling
        checkpoint_json = serialize_state(checkpoint_data)
        
        self.conn.execute("""
            INSERT INTO system_checkpoints (id, timestamp, checkpoint_data)
            VALUES (?, ?, ?)
        """, (checkpoint_id, now, checkpoint_json))
        
        return checkpoint_id
    
    def get_latest_checkpoint(self) -> Dict[str, Any]:
        """
        Get the latest system checkpoint.

        Returns:
            Checkpoint data
        """
        result = self.conn.execute("""
            SELECT * FROM system_checkpoints
            ORDER BY timestamp DESC
            LIMIT 1
        """).fetchone()

        if not result:
            return None

        # Convert result to dictionary
        columns = ["id", "timestamp", "checkpoint_data"]
        checkpoint = {columns[i]: result[i] for i in range(len(columns))}

        # Parse checkpoint data with datetime handling
        try:
            checkpoint["checkpoint_data"] = deserialize_state(checkpoint["checkpoint_data"])
        except (json.JSONDecodeError, TypeError):
            # Keep as is if not valid JSON
            pass

        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Get a system checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            Checkpoint data
        """
        result = self.conn.execute("""
            SELECT * FROM system_checkpoints
            WHERE id = ?
        """, (checkpoint_id,)).fetchone()

        if not result:
            return None

        # Convert result to dictionary
        columns = ["id", "timestamp", "checkpoint_data"]
        checkpoint = {columns[i]: result[i] for i in range(len(columns))}

        # Parse checkpoint data with datetime handling
        try:
            checkpoint["checkpoint_data"] = deserialize_state(checkpoint["checkpoint_data"])
        except (json.JSONDecodeError, TypeError):
            # Keep as is if not valid JSON
            pass

        return checkpoint

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None