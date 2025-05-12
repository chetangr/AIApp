# Multi-Agent Development System

A comprehensive Streamlit-based orchestration system using LangGraph that coordinates 7 specialized AI agents for automated software development.

## Overview

This system implements a multi-agent software development pipeline where specialized AI agents handle different aspects of the development process, from project management to error handling. The system maintains state through a DuckDB database and provides a user-friendly Streamlit interface for interaction.

## Key Features

- **Seven Specialized Agents**: Project Manager, Developer, UI/UX, Integration, Testing, Documentation, and Error Handling
- **DuckDB Persistence**: Stores all project data and enables system recovery
- **LangGraph Orchestration**: Coordinates agent workflows and handles message passing
- **Streamlit Interface**: Provides easy project creation, monitoring, and visualization
- **Claude API Integration**: Uses Anthropic's Claude API for intelligent project name extraction
- **Fallback Mechanisms**: Gracefully degrades to rule-based approaches when API is unavailable

## Project Structure

```
multi-agent-dev/
├── app.py                   # Main Streamlit application
├── agents/                  # Agent implementation modules
│   ├── project_manager.py
│   ├── developer.py
│   ├── ui_ux.py
│   ├── integration.py
│   ├── testing.py
│   ├── documentation.py
│   └── error_handling.py
├── core/                    # Core system components
│   ├── orchestration.py     # LangGraph setup
│   ├── database.py          # DuckDB integration
│   └── messaging.py         # Inter-agent communication
├── utils/                   # Utility functions
└── data/                    # Storage for DuckDB files
```

## Installation

1. Clone the repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. (Optional) Run the dependency installer to ensure all packages are properly installed:

```bash
python install_deps.py
```

4. (Optional) Configure API keys:
   - Create a `.env` file based on `.env.example`
   - Add your Anthropic API key for Claude integration
   - You can also enter your API key directly in the Streamlit interface

```
# .env file example
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

5. Run the Streamlit application:

```bash
streamlit run app.py
```

**Note:** If you encounter any missing dependency errors when running the app, run the installation script first:

```bash
python install_deps.py
```

## Usage

1. **Create a Project**: Define your project requirements through the user interface
2. **Monitor Progress**: Watch the agents collaborate on your project in real-time
3. **Review Outputs**: Examine code, designs, documentation, and test results
4. **Fix Errors**: Monitor and resolve any issues that arise

## Agent Descriptions

1. **Project Manager Agent**: Analyzes requirements, creates task lists, assigns work
2. **Developer Agent**: Generates implementation code for assigned tasks
3. **UI/UX Agent**: Designs and implements user interfaces
4. **Full-Stack Integration Agent**: Connects frontend and backend components
5. **Testing Agent**: Creates and executes tests for all components
6. **Documentation Agent**: Creates developer docs and user guides
7. **Error Handling Agent**: Monitors, diagnoses, and resolves errors across all agents

## System Architecture

The system uses a LangGraph-based orchestration layer that manages agent interactions through a message-passing system. Each agent has a specific role in the development pipeline, and the Project Manager coordinates the overall workflow. The DuckDB database provides persistence, allowing the system to resume work after interruptions.

## Future Enhancements

- Support for additional specialized agents
- Integration with GitHub for code management
- Enhanced visualization of agent interactions
- Real-time collaboration features