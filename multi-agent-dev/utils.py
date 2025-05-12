import os
import sys
import json
import datetime
import uuid

# Placeholder for logging function - this will be properly defined in app.py
# and imported here when the module is initialized
_log_agent_activity = None

def set_log_function(log_function):
    """Set the log_agent_activity function"""
    global _log_agent_activity
    _log_agent_activity = log_function

def log_agent_activity(agent_type, message):
    """Log agent activity using the function provided by app.py"""
    global _log_agent_activity
    if _log_agent_activity:
        _log_agent_activity(agent_type, message)
    else:
        # Fallback printing to console
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{agent_type}] {message}")

def format_timestamp(timestamp):
    """Format a timestamp for display"""
    if isinstance(timestamp, datetime.datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(timestamp, str):
        try:
            dt = datetime.datetime.fromisoformat(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return timestamp
    return str(timestamp)

def time_difference(timestamp):
    """Calculate time difference between now and timestamp"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.datetime.fromisoformat(timestamp)
        except ValueError:
            return "unknown"
    
    if isinstance(timestamp, datetime.datetime):
        now = datetime.datetime.now()
        diff = now - timestamp
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds/60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)} hours ago"
        else:
            return f"{int(seconds/86400)} days ago"
    
    return "unknown"

def truncate_text(text, max_length=100):
    """Truncate text to maximum length"""
    if text and len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def generate_id():
    """Generate a unique ID"""
    return str(uuid.uuid4())

class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

def serialize_state(state):
    """Serialize state dictionary to JSON string with datetime handling"""
    try:
        return json.dumps(state, cls=DateTimeEncoder)
    except Exception as e:
        print(f"Error serializing state: {str(e)}")
        return json.dumps({"error": f"Could not serialize state: {str(e)}"})

def deserialize_state(state_json):
    """Deserialize JSON string to state dictionary"""
    try:
        return json.loads(state_json)
    except Exception as e:
        print(f"Error deserializing state: {str(e)}")
        return {"error": f"Could not deserialize state: {str(e)}"}