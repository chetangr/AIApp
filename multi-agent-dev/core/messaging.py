import datetime
import uuid
import sys
import os.path
import json
from typing import Dict, Any, List, Optional

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import datetime-safe serialization functions
from utils import serialize_state, deserialize_state

class Message:
    """
    Message class for inter-agent communication.
    """
    def __init__(self, 
                 sender_id: str, 
                 receiver_id: str, 
                 content: Any,
                 message_type: str = "task",
                 task_id: Optional[str] = None,
                 project_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a message.
        
        Args:
            sender_id: ID of the sending agent
            receiver_id: ID of the receiving agent
            content: Message content (can be any serializable data)
            message_type: Type of message (task, response, error, etc.)
            task_id: Optional task ID associated with the message
            project_id: Optional project ID associated with the message
            metadata: Optional additional metadata
        """
        self.id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.content = content
        self.message_type = message_type
        self.task_id = task_id
        self.project_id = project_id
        self.metadata = metadata or {}
        self.timestamp = datetime.datetime.now()
        self.read = False
        self.processed = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary with serializable values.

        Returns:
            Dictionary representation of the message
        """
        # Convert basic properties
        result = {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "read": self.read,
            "processed": self.processed
        }

        # Handle content separately to ensure it's serializable
        if isinstance(self.content, (dict, list)):
            # Use serialize_state to handle any datetime objects
            try:
                result["content"] = json.loads(serialize_state(self.content))
            except Exception as e:
                # If serialization fails, use string representation
                result["content"] = {"content_error": f"Could not serialize: {str(e)}"}
        else:
            # For non-object content, use as is
            result["content"] = self.content

        # Handle metadata separately
        if self.metadata:
            try:
                result["metadata"] = json.loads(serialize_state(self.metadata))
            except Exception as e:
                result["metadata"] = {"metadata_error": f"Could not serialize: {str(e)}"}
        else:
            result["metadata"] = {}

        # Convert timestamp to ISO format
        try:
            result["timestamp"] = self.timestamp.isoformat()
        except Exception as e:
            result["timestamp"] = str(self.timestamp)

        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create message from dictionary.
        
        Args:
            data: Dictionary representation of a message
            
        Returns:
            Message instance
        """
        message = cls(
            sender_id=data.get("sender_id"),
            receiver_id=data.get("receiver_id"),
            content=data.get("content"),
            message_type=data.get("message_type"),
            task_id=data.get("task_id"),
            project_id=data.get("project_id"),
            metadata=data.get("metadata")
        )
        message.id = data.get("id", message.id)
        message.timestamp = data.get("timestamp", message.timestamp)
        message.read = data.get("read", message.read)
        message.processed = data.get("processed", message.processed)
        return message


class MessageBus:
    """
    Message bus for handling inter-agent communication.
    """
    def __init__(self, db_connector=None):
        """
        Initialize the message bus.
        
        Args:
            db_connector: Optional database connector for message persistence
        """
        self.db_connector = db_connector
        self.message_queue: Dict[str, List[Message]] = {}  # receiver_id -> [messages]
        self.message_history: List[Message] = []  # All messages
    
    def send_message(self, message: Message) -> str:
        """
        Send a message to a receiver.
        
        Args:
            message: Message to send
            
        Returns:
            Message ID
        """
        # Add to receiver's queue
        if message.receiver_id not in self.message_queue:
            self.message_queue[message.receiver_id] = []
        self.message_queue[message.receiver_id].append(message)
        
        # Add to history
        self.message_history.append(message)
        
        # Persist message if database connector available
        if self.db_connector:
            # Ensure the message content is JSON serializable
            try:
                # First serialize to catch any datetime issues
                message_dict = message.to_dict()
                json_safe_dict = json.loads(serialize_state(message_dict))

                # Make sure we have a valid task_id (not "system")
                task_id = message.task_id
                if not task_id or task_id == "system":
                    # Try to get a valid task ID for this project
                    try:
                        system_tasks = self.db_connector.get_tasks_by_project(message.project_id)
                        if system_tasks:
                            # Use the first available task
                            task_id = system_tasks[0]["id"]
                        else:
                            # Create a system task for logging
                            task_id = self.db_connector.create_task(
                                project_id=message.project_id,
                                title="System Task",
                                description="System-generated task for logging purposes",
                                assigned_agent="system"
                            )
                    except Exception as task_error:
                        # Log error but continue without storing
                        print(f"Error getting valid task ID: {str(task_error)}")
                        return message.id

                # Now store with valid task_id
                self.db_connector.store_agent_output(
                    task_id=task_id,
                    agent_id=message.sender_id,
                    output_type=f"message_{message.message_type}",
                    content=json_safe_dict
                )
            except Exception as e:
                # If serialization fails, store a simplified message
                print(f"Warning: Could not serialize message - {str(e)}")

                # Make sure we have a valid task_id (not "system")
                task_id = message.task_id
                if not task_id or task_id == "system":
                    # Try to get a valid task ID for this project
                    try:
                        system_tasks = self.db_connector.get_tasks_by_project(message.project_id)
                        if system_tasks:
                            # Use the first available task
                            task_id = system_tasks[0]["id"]
                        else:
                            # Skip storing since we can't create a task during error handling
                            return message.id
                    except Exception:
                        # Skip storing if we can't get a valid task
                        return message.id

                # Store simplified message with valid task_id
                try:
                    self.db_connector.store_agent_output(
                        task_id=task_id,
                        agent_id=message.sender_id,
                        output_type=f"message_{message.message_type}",
                        content={"message_id": message.id, "error": str(e)}
                    )
                except Exception as store_error:
                    # If we still can't store, just log and continue
                    print(f"Error storing message: {str(store_error)}")
        
        return message.id
    
    def get_messages(self, receiver_id: str, mark_read: bool = True) -> List[Message]:
        """
        Get messages for a receiver.
        
        Args:
            receiver_id: Receiver ID
            mark_read: Whether to mark messages as read
            
        Returns:
            List of messages
        """
        if receiver_id not in self.message_queue:
            return []
        
        messages = self.message_queue[receiver_id]
        
        if mark_read:
            for message in messages:
                message.read = True
        
        return messages
    
    def get_unread_messages(self, receiver_id: str, mark_read: bool = True) -> List[Message]:
        """
        Get unread messages for a receiver.
        
        Args:
            receiver_id: Receiver ID
            mark_read: Whether to mark messages as read
            
        Returns:
            List of unread messages
        """
        if receiver_id not in self.message_queue:
            return []
        
        unread_messages = [m for m in self.message_queue[receiver_id] if not m.read]
        
        if mark_read:
            for message in unread_messages:
                message.read = True
        
        return unread_messages
    
    def mark_processed(self, message_id: str) -> bool:
        """
        Mark a message as processed.
        
        Args:
            message_id: Message ID
            
        Returns:
            True if message was found and marked, False otherwise
        """
        # Check all queues
        for queue in self.message_queue.values():
            for message in queue:
                if message.id == message_id:
                    message.processed = True
                    return True
        
        # Check history as fallback
        for message in self.message_history:
            if message.id == message_id:
                message.processed = True
                return True
        
        return False
    
    def get_message_history(self, task_id: Optional[str] = None, 
                          project_id: Optional[str] = None,
                          sender_id: Optional[str] = None,
                          receiver_id: Optional[str] = None) -> List[Message]:
        """
        Get message history with optional filters.
        
        Args:
            task_id: Optional task ID filter
            project_id: Optional project ID filter
            sender_id: Optional sender ID filter
            receiver_id: Optional receiver ID filter
            
        Returns:
            Filtered message history
        """
        history = self.message_history
        
        # Apply filters
        if task_id:
            history = [m for m in history if m.task_id == task_id]
        if project_id:
            history = [m for m in history if m.project_id == project_id]
        if sender_id:
            history = [m for m in history if m.sender_id == sender_id]
        if receiver_id:
            history = [m for m in history if m.receiver_id == receiver_id]
        
        return history
    
    def broadcast(self, sender_id: str, receivers: List[str], content: Any, 
                 message_type: str = "broadcast", task_id: Optional[str] = None,
                 project_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Broadcast a message to multiple receivers.
        
        Args:
            sender_id: Sender ID
            receivers: List of receiver IDs
            content: Message content
            message_type: Message type
            task_id: Optional task ID
            project_id: Optional project ID
            metadata: Optional metadata
            
        Returns:
            List of message IDs
        """
        message_ids = []
        
        for receiver_id in receivers:
            message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                message_type=message_type,
                task_id=task_id,
                project_id=project_id,
                metadata=metadata
            )
            message_id = self.send_message(message)
            message_ids.append(message_id)
        
        return message_ids
    
    def clear_processed_messages(self):
        """Remove processed messages from queues."""
        for receiver_id in self.message_queue:
            self.message_queue[receiver_id] = [
                m for m in self.message_queue[receiver_id] if not m.processed
            ]