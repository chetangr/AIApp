```
Implement a multi-agent software development system with the following specifications:

# Multi-Agent Software Development System Specifications

## Project Overview
Create a Streamlit-based orchestration system using LangGraph that coordinates 7 specialized AI agents for automated software development. Implement local state persistence with DuckDB and design an extensible architecture.

## Core Components

1. Seven specialized agents with clear responsibilities:
   - Project Manager Agent: Analyzes requirements, creates task lists, assigns work
   - Developer Agent: Generates implementation code for assigned tasks
   - UI/UX Agent: Designs and implements user interfaces
   - Full-Stack Integration Agent: Connects frontend and backend components
   - Testing Agent: Creates and executes tests for all components
   - Documentation Agent: Creates developer docs and user guides
   - Error Handling Agent: Monitors, diagnoses, and resolves errors across all agents

2. DuckDB persistence layer that:
   - Stores all project data, tasks, and agent outputs
   - Enables resuming work after system restarts
   - Tracks progress with timestamps and status updates

3. Streamlit interface featuring:
   - Project creation form for initial requirements
   - Real-time dashboard showing project status
   - Detailed views of each agent's outputs
   - Task tracking with progress visualization
   - Error monitoring and resolution interface

4. LangGraph orchestration that:
   - Implements a hierarchical workflow with the Project Manager as coordinator
   - Handles message passing between agents
   - Manages state transitions and error recovery
   - Enables checkpointing for persistence

## Project Structure
Create this directory structure:
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

## Database Schema
Implement this schema in DuckDB:
```sql
CREATE TABLE projects (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE tasks (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR,
    title VARCHAR NOT NULL,
    description TEXT,
    assigned_agent VARCHAR,
    status VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE agent_outputs (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR,
    agent_id VARCHAR,
    output_type VARCHAR,
    content TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE errors (
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
);

CREATE TABLE system_checkpoints (
    id VARCHAR PRIMARY KEY,
    timestamp TIMESTAMP,
    checkpoint_data TEXT
);
```

## Agent Specifications

1. Project Manager Agent:
   - Input: Project requirements as natural language
   - Output: Structured task breakdown with assignments
   - Core functions: parse_requirements(), create_task_breakdown(), assign_tasks_to_agents(), monitor_progress()
   - System prompt: "You are an expert Project Manager agent responsible for analyzing requirements, breaking them into manageable tasks, and coordinating work among specialized development agents..."

2. Developer Agent:
   - Input: Task description, required technologies, dependencies
   - Output: Implementation code, explanatory comments
   - Core functions: analyze_task_requirements(), generate_implementation_code(), document_code()
   - System prompt: "You are an expert Developer agent responsible for implementing high-quality code based on task specifications..."

3. UI/UX Agent:
   - Input: Interface requirements, brand guidelines, user stories
   - Output: UI component code (HTML, CSS, JS, React, etc.)
   - Core functions: design_interface_components(), implement_responsive_design(), ensure_accessibility_compliance()
   - System prompt: "You are an expert UI/UX agent responsible for creating intuitive, accessible user interfaces..."

4. Full-Stack Integration Agent:
   - Input: Frontend components, backend services, API specs
   - Output: Integration code, connection handlers
   - Core functions: analyze_component_interfaces(), implement_data_flow(), create_api_connectors()
   - System prompt: "You are an expert Full-Stack Integration agent responsible for connecting frontend and backend components..."

5. Testing Agent:
   - Input: Implementation code, requirements, expected behaviors
   - Output: Test suites, test results, bug reports
   - Core functions: generate_test_cases(), execute_tests(), generate_test_report()
   - System prompt: "You are an expert Testing agent responsible for verifying the functionality and quality of implementations..."

6. Documentation Agent:
   - Input: Codebase, requirements, test results
   - Output: Developer docs, user guides, API documentation
   - Core functions: analyze_codebase(), generate_technical_documentation(), create_user_guides()
   - System prompt: "You are an expert Documentation agent responsible for creating clear, comprehensive documentation..."

7. Error Handling Agent:
   - Input: Error messages, stack traces, agent outputs
   - Output: Error diagnostics, solution recommendations, fixes
   - Core functions: analyze_error(), identify_root_cause(), generate_fix(), implement_recovery_strategy()
   - System prompt: "You are an expert Error Handling agent responsible for diagnosing, resolving, and preventing errors across the entire development pipeline..."
   - Special capabilities: Can intercept workflow when errors occur, recommend fixes to other agents, and verify solutions

## LangGraph Implementation
Use LangGraph to:
1. Define a StateGraph with nodes for each agent
2. Create state schemas for agent communication
3. Implement transitions between agents based on task dependencies
4. Add checkpoint persistence using DuckDB
5. Implement error handling pathways that route to the Error Handling Agent

## Streamlit Interface
Build a Streamlit app with:
1. Project creation form for inputting requirements
2. Dashboard showing overall project status
3. Task board with status tracking
4. Agent output viewer with formatted code display
5. Progress visualization with metrics and charts
6. Error monitoring dashboard with resolution status
7. System health indicators

## Implementation Steps
1. Set up the project structure and install dependencies
2. Implement the DuckDB integration and database schema
3. Create the agent prompt templates and basic functions
4. Build the LangGraph orchestration layer
5. Implement the Streamlit interface
6. Add state persistence and checkpoint recovery
7. Implement the Error Handling Agent with monitoring capabilities
8. Create documentation and usage examples

Create detailed, well-commented code with proper error handling throughout the system. Design the system to be modular so additional agents can be added in the future. Optimize for local execution with minimal resource usage.
```

The Error Handling Agent adds a critical layer of reliability by:

1. Monitoring for errors across all agent interactions
2. Diagnosing root causes when failures occur
3. Generating appropriate fixes or workarounds
4. Implementing recovery strategies to get back on track
5. Tracking error patterns to prevent recurring issues

I've also added an errors table to the database schema to track error history, and expanded the Streamlit interface to include an error monitoring dashboard. This agent will significantly improve the system's robustness and ability to recover from failures.