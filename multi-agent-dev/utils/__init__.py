from datetime import datetime, timedelta
import uuid
import json
import traceback
from typing import Dict, Any, List, Optional, Union, Callable

# Store for log function
_log_agent_activity = None

def set_log_function(log_function: Callable):
    """Set the log_agent_activity function"""
    global _log_agent_activity
    _log_agent_activity = log_function

def log_agent_activity(agent_type: str, message: str):
    """Log agent activity using the provided log function"""
    global _log_agent_activity
    if _log_agent_activity:
        _log_agent_activity(agent_type, message)
    else:
        # Fallback printing to console
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{agent_type}] {message}")

def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())

def timestamp_now() -> datetime:
    """Get current timestamp."""
    return datetime.now()

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def time_difference(start: datetime, end: Optional[datetime] = None) -> str:
    """Calculate human-readable time difference."""
    if end is None:
        end = datetime.now()
    
    diff = end - start
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours"
    else:
        return f"{int(seconds / 86400)} days"

def serialize_state(state: Dict[str, Any]) -> str:
    """Serialize state to JSON string with datetime handling."""
    def datetime_handler(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle other non-serializable types
        try:
            # Try to convert to string
            return str(obj)
        except:
            # If all else fails
            return f"<non-serializable: {type(obj).__name__}>"

    return json.dumps(state, default=datetime_handler)

def deserialize_state(state_json: str) -> Dict[str, Any]:
    """Deserialize state from JSON string with datetime handling."""
    def datetime_parser(dct):
        for k, v in dct.items():
            if isinstance(v, str):
                try:
                    dct[k] = datetime.fromisoformat(v)
                except (ValueError, TypeError):
                    pass
        return dct
    
    return json.loads(state_json, object_hook=datetime_parser)

def sanitize_input(input_str: str) -> str:
    """Sanitize user input."""
    # Simple sanitization - a real implementation would be more comprehensive
    return input_str.strip()

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_error(error: Exception) -> Dict[str, str]:
    """Format exception into a structured error dictionary."""
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "stack_trace": traceback.format_exc()
    }

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries with nested support."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result