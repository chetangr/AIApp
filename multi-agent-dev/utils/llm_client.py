"""
LLM Client utilities for making API calls to Claude
"""
import os
from typing import Dict, List, Optional, Any
import logging
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if python-dotenv is available
dotenv_available = importlib.util.find_spec("dotenv") is not None
if dotenv_available:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
else:
    logger.warning("python-dotenv is not installed. Environment variables will not be loaded from .env file.")

# Check if anthropic is available
anthropic_available = importlib.util.find_spec("anthropic") is not None
if anthropic_available:
    from anthropic import Anthropic
    logger.info("Anthropic library is available")
else:
    logger.warning("Anthropic library not installed. Claude API features will not be available.")

class ClaudeClient:
    """Client for interacting with Claude API"""

    def __init__(self):
        """Initialize Claude client with API key from environment variables"""
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        # If Anthropic library is not available, we can't proceed
        if not anthropic_available:
            logger.warning("Anthropic library not available. Claude features will not work.")
            return

        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment variables. Claude features will not work.")
            return

        try:
            self.client = Anthropic(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            self.client = None
    
    def configure(self, api_key: str):
        """
        Configure the client with a new API key
        
        Args:
            api_key: Anthropic API key
        """
        if not api_key:
            logger.warning("Empty API key provided")
            return
            
        self.api_key = api_key
        os.environ["ANTHROPIC_API_KEY"] = api_key
        
        # If Anthropic library is not available, we can't proceed
        if not anthropic_available:
            logger.warning("Anthropic library not available. Claude features will not work.")
            return
            
        try:
            self.client = Anthropic(api_key=api_key)
            logger.info("Anthropic client successfully configured")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {str(e)}")
            self.client = None
        
    def is_available(self) -> bool:
        """Check if the Claude client is properly configured"""
        return self.client is not None
    
    def extract_project_name(self, requirements: str) -> str:
        """
        Use Claude to extract a suitable project name from the requirements
        
        Args:
            requirements: String containing the project requirements
            
        Returns:
            Extracted project name as a string
        """
        if not self.is_available():
            logger.warning("Claude client not available. Using fallback method for project name.")
            # Import the fallback function from get_project_name.py
            from get_project_name import get_project_name_from_requirements
            return get_project_name_from_requirements(requirements)
        
        try:
            # Check again that the client is available and Anthropic library is imported
            if not anthropic_available or not self.client:
                raise ImportError("Anthropic library or client not available")

            # Create a system prompt that asks Claude to extract a project name
            system_prompt = """
            Extract a suitable project name from the requirements provided by the user.
            The project name should be:
            1. Descriptive of the project's main purpose
            2. Short (1-3 words)
            3. Formatted in snake_case (lowercase with underscores)
            4. Not contain any special characters other than underscores

            Respond with ONLY the project name in snake_case format. No explanations or other text.
            """

            # Call Claude API
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                system=system_prompt,
                max_tokens=30,
                messages=[
                    {"role": "user", "content": requirements}
                ]
            )
            
            # Extract and clean the project name
            project_name = message.content[0].text.strip()
            # Remove any non-alphanumeric characters except underscores
            import re
            project_name = re.sub(r'[^\w_]', '', project_name)
            # Ensure snake_case format
            project_name = project_name.lower().replace(' ', '_')
            
            logger.info(f"Extracted project name using Claude: {project_name}")
            return project_name
            
        except ImportError as e:
            logger.error(f"Anthropic library import error: {str(e)}")
            logger.info("Falling back to local project name extraction")
            from get_project_name import get_project_name_from_requirements
            return get_project_name_from_requirements(requirements)
        except ModuleNotFoundError as e:
            logger.error(f"Module not found: {str(e)}")
            logger.info("Falling back to local project name extraction")
            from get_project_name import get_project_name_from_requirements
            return get_project_name_from_requirements(requirements)
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            logger.info("Falling back to local project name extraction")
            from get_project_name import get_project_name_from_requirements
            return get_project_name_from_requirements(requirements)

# Initialize global client
claude_client = ClaudeClient()