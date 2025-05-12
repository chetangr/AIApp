import os
import sys
from core.database import DatabaseConnector
from core.orchestration_simple import SimpleOrchestrator

def main():
    print("Testing Multi-Agent Development System")

    # Create a temporary database path
    tmp_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "temp_test.duckdb")

    # Create database connector with temporary path
    db_connector = DatabaseConnector(db_path=tmp_db_path)
    
    # Create orchestrator
    orchestrator = SimpleOrchestrator(db_connector=db_connector)
    
    # Initialize a project
    project_requirements = """
    Create a pet diary mobile app for Android. The app should allow users to:
    1. Track pet activities like feeding, walking, grooming
    2. Store vet visit records
    3. Set reminders for pet care tasks
    4. Upload and store pictures of pets
    5. Generate reports of pet activities
    """
    
    print("Creating project with requirements...")
    project_id = orchestrator.initialize_project(
        name="Pet Diary App",
        description="A mobile app for tracking pet care activities",
        requirements=project_requirements
    )
    
    print(f"Project created with ID: {project_id}")
    
    # Run the orchestration
    print("Running orchestration...")
    state = orchestrator.run(steps=5)
    
    print("Orchestration complete!")
    
    # Check project status
    status = orchestrator.get_project_status(project_id)
    print(f"Project Status: {status['project']['status']}")
    print(f"Tasks: Total={status['tasks']['total']}, Completed={status['tasks']['completed']}")
    
    # Create project directories
    projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects")
    os.makedirs(projects_dir, exist_ok=True)
    
    # Print completion message
    print("\nTest complete! Check the projects directory for created files.")

if __name__ == "__main__":
    main()