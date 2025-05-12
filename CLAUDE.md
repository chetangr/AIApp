# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a multi-agent software development system that uses Streamlit, LangGraph, and DuckDB to coordinate seven specialized AI agents for automated software development. The system allows users to input project requirements and have AI agents collaborate to create a software project.

## Commands

### Running the Application

```bash
# Run the main application via the shell script
./multi-agent-dev/run.sh

# Or run directly with Streamlit 
cd multi-agent-dev
streamlit run app.py
```

### Testing the System

```bash
# Run the test system (creates a temporary project)
cd multi-agent-dev
python test_system.py
```

### Creating a Project Programmatically

```bash
# Create a new project with requirements
cd multi-agent-dev
python create_project.py --name "Project Name" --description "Project Description" --requirements "Project requirements text"
```

### Installing Dependencies

```bash
# Install required packages
cd multi-agent-dev
pip install -r requirements.txt

# Or use the dependency installer
python install_deps.py
```

## System Architecture

The system uses a multi-agent architecture with these components:

1. **Database Layer** - DuckDB for persistence with tables for projects, tasks, agent outputs, errors, and system checkpoints.

2. **Agent System** - Seven specialized agents (Project Manager, Developer, UI/UX, Integration, Testing, Documentation, Error Handling) that collaborate on software development tasks.

3. **Orchestration** - SimpleOrchestrator that manages message passing between agents and maintains system state.

4. **User Interface** - Streamlit app for project creation, task monitoring, and visualizing agent activity.

## Data Flow

1. User inputs requirements through the Streamlit interface
2. Project Manager Agent analyzes requirements and creates tasks
3. Tasks are assigned to specialized agents based on their roles
4. Agents process tasks and store results in the database
5. UI displays task progress and agent outputs in real-time

## API Integration

The system integrates with Claude API for project name extraction, with a fallback mechanism when the API is unavailable. The Anthropic API key has been provided and is ready to use.

## File Structure

- `app.py` - Main Streamlit application
- `agents/` - Contains the implementation of the 7 specialized agents
- `core/` - Core system components (orchestration, database, messaging)
- `utils/` - Utility functions (LLM client, serialization)
- `data/` - Storage for DuckDB database files
- `projects/` - Output directory for generated project files