"""
Task execution logic for the multi-agent system.
This module contains functions for running tasks and handling agent outputs.
"""
import os
import re
import sys
import subprocess
import streamlit as st
from typing import Dict, Any, List, Optional, Union, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import utility functions
from utils import log_agent_activity
from templates.project_utils import create_app_from_task, get_app_name_from_task, get_project_type, get_project_dir

def run_task(task_id):
    """
    Execute a task by its ID.
    
    Args:
        task_id: Task ID to run
        
    Returns:
        True if task was executed successfully, False otherwise
    """
    # Get task data
    task = None
    for t in st.session_state.tasks:
        if t.get("id") == task_id:
            task = t
            break
    
    if not task:
        log_agent_activity("system", f"Task {task_id} not found")
        return False
    
    # Mark task as in progress
    task["status"] = "in_progress"
    
    # Get agent type
    agent_type = task.get("assigned_agent", "developer")
    log_agent_activity(agent_type, f"Starting task: {task.get('title', 'Untitled Task')}")
    
    try:
        # Get project directory - ensuring consistency across all tasks
        project_dir = get_project_dir()
        
        # Execute task based on agent type
        if agent_type == "developer":
            # Implement developer tasks - create code from requirements
            result = create_app_from_task(task, agent_type)
            project_dir = result.get("project_dir")
            
            # Run build command if applicable
            project_type = result.get("project_type")
            if project_type and project_dir and os.path.exists(project_dir):
                run_build_command(project_dir, project_type)
            
        elif agent_type == "ui_ux":
            # Implement UI/UX tasks - typically handled in the Flutter or React app creation
            result = create_app_from_task(task, agent_type)
            project_dir = result.get("project_dir")
            
            # After creating the basic UI, we can run specific UI/UX tasks
            if project_dir:
                project_type = get_project_type(task)
                customize_ui_components(project_dir, project_type, task)
        
        elif agent_type == "testing":
            # Create test files
            project_type = get_project_type(task)
            
            # Use the common project directory for all tasks
            project_dir = get_project_dir()
            
            # Create test files if they don't exist
            os.makedirs(os.path.join(project_dir, "test"), exist_ok=True)
            
            # Create widget test file
            test_file = os.path.join(project_dir, "test", "widget_test.dart")
            test_content = """import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import '../lib/main.dart';

void main() {
  testWidgets('App should launch and display correctly', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that our app builds without errors
    expect(find.byType(MaterialApp), findsOneWidget);
    
    // Basic UI verification
    expect(find.byType(AppBar), findsOneWidget);
  });
}
"""
            with open(test_file, "w") as f:
                f.write(test_content)
            
            log_agent_activity(agent_type, f"Created test file: {test_file}")
            
            # Run tests if the project type is Flutter
            if project_type == "flutter":
                run_flutter_tests(project_dir)
            
            # Create a test plan
            test_plan_file = os.path.join(project_dir, "test", "test_plan.md")
            test_plan_content = f"""# Test Plan

## Test Scope
- Unit tests for core functionality
- Widget tests for UI components
- Integration tests for key workflows

## Test Strategy
- Focus on critical features first
- Automated tests for regression testing
- Manual testing for complex UI interactions

## Test Cases
1. Application launch and initialization
2. Navigation between screens
3. Data persistence
4. Form validation
5. Error handling

## Test Environment
- Flutter test framework
- Mock data for database tests
- Different device sizes for UI testing
"""
            with open(test_plan_file, "w") as f:
                f.write(test_plan_content)
            
            log_agent_activity(agent_type, f"Created test plan: {test_plan_file}")
            
        elif agent_type == "documentation":
            # Create documentation
            project_name = None
            
            # Get the project name from session state
            if "project_name" in st.session_state and st.session_state.project_name:
                project_name = st.session_state.project_name
            
            # Use the common project directory
            project_dir = get_project_dir()
            
            if not project_name:
                # Derive from project directory
                project_name = os.path.basename(project_dir).lower()
            
            project_name_display = project_name.replace("_", " ").title()
            
            # Create README file
            readme_file = os.path.join(project_dir, "README.md")
            project_requirements = task.get("description", "A software project")
            
            readme_content = f"""# {project_name_display}

{project_requirements}

## Features

- Feature 1
- Feature 2
- Feature 3

## Getting Started

### Prerequisites

- Flutter SDK (for mobile projects)
- Android Studio / Xcode (for deployment)

### Installation

1. Clone this repository
2. Navigate to the project directory
3. Run `flutter pub get` to install dependencies
4. Run `flutter run` to start the app

## Project Structure

- `lib/`: Contains the main Dart code
  - `screens/`: UI screens
  - `widgets/`: Reusable UI components
  - `models/`: Data models
  - `services/`: Business logic and API services
  - `utils/`: Utility functions
  - `theme/`: App theme definition

## Screenshots

(Screenshots will be added once the app is fully developed)

## Testing

Run `flutter test` to execute the test suite.
"""
            with open(readme_file, "w") as f:
                f.write(readme_content)
            
            log_agent_activity(agent_type, f"Created README: {readme_file}")
            
            # Create a user guide
            docs_dir = os.path.join(project_dir, "docs")
            os.makedirs(docs_dir, exist_ok=True)
            
            user_guide_file = os.path.join(docs_dir, "user_guide.md")
            user_guide_content = f"""# User Guide for {project_name_display}

## Getting Started

### Installation
1. Download the app from the app store
2. Open the app
3. Create an account or log in

### Main Features

#### Feature 1
Description of feature 1 and how to use it.

#### Feature 2
Description of feature 2 and how to use it.

#### Feature 3
Description of feature 3 and how to use it.

## Troubleshooting

### Common Issues
- Issue 1: Solution for issue 1
- Issue 2: Solution for issue 2
- Issue 3: Solution for issue 3

## Contact Support
If you need help, please contact us at support@example.com
"""
            with open(user_guide_file, "w") as f:
                f.write(user_guide_content)
            
            log_agent_activity(agent_type, f"Created user guide: {user_guide_file}")
            
            # Generate API documentation if it's a Flutter project
            project_type = get_project_type(task)
            if project_type == "flutter" and os.path.exists(os.path.join(project_dir, "lib")):
                generate_api_docs(project_dir)
        
        elif agent_type == "integration":
            # Implement integration tasks
            project_type = get_project_type(task)
            
            # Use the common project directory
            project_dir = get_project_dir()
                
            if project_type == "flutter":
                # Create API service
                os.makedirs(os.path.join(project_dir, "lib", "services"), exist_ok=True)
                api_service_file = os.path.join(project_dir, "lib", "services", "api_service.dart")
                api_service_content = """import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  final Map<String, String> headers;

  ApiService({
    required this.baseUrl,
    this.headers = const {
      'Content-Type': 'application/json',
    },
  });

  Future<dynamic> get(String endpoint) async {
    final response = await http.get(
      Uri.parse('$baseUrl/$endpoint'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load data: ${response.statusCode}');
    }
  }

  Future<dynamic> post(String endpoint, Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/$endpoint'),
      headers: headers,
      body: json.encode(data),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to post data: ${response.statusCode}');
    }
  }

  Future<dynamic> put(String endpoint, Map<String, dynamic> data) async {
    final response = await http.put(
      Uri.parse('$baseUrl/$endpoint'),
      headers: headers,
      body: json.encode(data),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to update data: ${response.statusCode}');
    }
  }

  Future<void> delete(String endpoint) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/$endpoint'),
      headers: headers,
    );

    if (response.statusCode != 200 && response.statusCode != 204) {
      throw Exception('Failed to delete data: ${response.statusCode}');
    }
  }
}
"""
                with open(api_service_file, "w") as f:
                    f.write(api_service_content)
                
                log_agent_activity(agent_type, f"Created API service: {api_service_file}")
                
                # Update pubspec.yaml to include http package if needed
                update_dependencies(project_dir, project_type, ["http"])
                
                # Run flutter pub get to install dependencies
                run_dependency_installation(project_dir, project_type)
            
            elif project_type in ["react", "web"]:
                integrate_react_components(project_dir, task)
        
        elif agent_type == "error_handling":
            # Implement error handling tasks
            project_type = get_project_type(task)
            
            # Use the common project directory
            project_dir = get_project_dir()
            
            if os.path.exists(project_dir):
                # Add error handling based on project type
                if project_type == "flutter":
                    add_flutter_error_handling(project_dir)
                elif project_type in ["react", "web"]:
                    add_react_error_handling(project_dir)
            
            log_agent_activity(agent_type, f"Added error handling to project in {project_dir}")
            
        else:
            # For other agent types, just log the activity
            log_agent_activity(agent_type, f"Processing task: {task.get('title', 'Untitled Task')}")
        
        # Mark task as completed
        task["status"] = "completed"
        log_agent_activity(agent_type, f"Completed task: {task.get('title', 'Untitled Task')}")
        
        # Return success
        return True
    
    except Exception as e:
        # Handle exception
        import traceback
        log_agent_activity(agent_type, f"Error executing task: {str(e)}")
        log_agent_activity("error_handling", traceback.format_exc())
        
        # Mark task as error
        task["status"] = "error"
        
        # Return failure
        return False

def run_build_command(project_dir, project_type):
    """Run appropriate build command based on project type"""
    try:
        log_agent_activity("developer", f"Running build command for {project_type} project")
        
        if project_type == "flutter":
            # Run flutter build to generate a release build
            subprocess.run(
                ["flutter", "build", "apk", "--release"], 
                check=True, 
                cwd=project_dir,
                capture_output=True
            )
            log_agent_activity("developer", "Successfully built Flutter APK")
            
        elif project_type in ["react", "web"]:
            # Check if package.json exists
            if os.path.exists(os.path.join(project_dir, "package.json")):
                # Install dependencies first
                subprocess.run(
                    ["npm", "install"], 
                    check=True, 
                    cwd=project_dir,
                    capture_output=True
                )
                
                # Run build command
                subprocess.run(
                    ["npm", "run", "build"], 
                    check=True, 
                    cwd=project_dir,
                    capture_output=True
                )
                log_agent_activity("developer", "Successfully built React app")
                
        elif project_type == "python_backend":
            # For Python, we create a virtual environment and install dependencies
            venv_dir = os.path.join(project_dir, "venv")
            
            # Create virtual environment if it doesn't exist
            if not os.path.exists(venv_dir):
                subprocess.run(
                    ["python3", "-m", "venv", "venv"], 
                    check=True, 
                    cwd=project_dir,
                    capture_output=True
                )
            
            # Install dependencies if setup.py exists
            if os.path.exists(os.path.join(project_dir, "setup.py")):
                if os.name == "nt":  # Windows
                    pip_cmd = os.path.join(venv_dir, "Scripts", "pip")
                else:  # Unix/MacOS
                    pip_cmd = os.path.join(venv_dir, "bin", "pip")
                    
                subprocess.run(
                    [pip_cmd, "install", "-e", "."], 
                    check=True, 
                    cwd=project_dir,
                    capture_output=True
                )
                log_agent_activity("developer", "Successfully installed Python package")
        
        return True
        
    except subprocess.CalledProcessError as e:
        log_agent_activity("error_handling", f"Build command failed: {str(e)}")
        log_agent_activity("error_handling", f"Output: {e.stdout.decode() if e.stdout else ''}")
        log_agent_activity("error_handling", f"Error: {e.stderr.decode() if e.stderr else ''}")
        return False
    except Exception as e:
        log_agent_activity("error_handling", f"Error running build command: {str(e)}")
        return False

def run_dependency_installation(project_dir, project_type):
    """Run appropriate dependency installation command based on project type"""
    try:
        log_agent_activity("developer", f"Installing dependencies for {project_type} project")
        
        if project_type == "flutter":
            # Run flutter pub get to install dependencies
            subprocess.run(
                ["flutter", "pub", "get"], 
                check=True, 
                cwd=project_dir,
                capture_output=True
            )
            log_agent_activity("developer", "Successfully installed Flutter dependencies")
            
        elif project_type in ["react", "web"]:
            # Install npm dependencies
            if os.path.exists(os.path.join(project_dir, "package.json")):
                subprocess.run(
                    ["npm", "install"], 
                    check=True, 
                    cwd=project_dir,
                    capture_output=True
                )
                log_agent_activity("developer", "Successfully installed npm dependencies")
        
        return True
        
    except subprocess.CalledProcessError as e:
        log_agent_activity("error_handling", f"Dependency installation failed: {str(e)}")
        return False
    except Exception as e:
        log_agent_activity("error_handling", f"Error installing dependencies: {str(e)}")
        return False

def update_dependencies(project_dir, project_type, dependencies):
    """Add dependencies to the project"""
    try:
        if project_type == "flutter":
            # Update pubspec.yaml to add dependencies
            pubspec_path = os.path.join(project_dir, "pubspec.yaml")
            if os.path.exists(pubspec_path):
                with open(pubspec_path, 'r') as f:
                    pubspec_content = f.read()
                
                # Find the dependencies section
                deps_section = "dependencies:\n  flutter:\n    sdk: flutter"
                updated_deps = deps_section
                
                # Add each dependency if not already present
                for dep in dependencies:
                    if dep == "http" and "http:" not in pubspec_content:
                        updated_deps += f"\n  http: ^1.1.0"
                    elif dep == "provider" and "provider:" not in pubspec_content:
                        updated_deps += f"\n  provider: ^6.0.5"
                    elif dep == "sqflite" and "sqflite:" not in pubspec_content:
                        updated_deps += f"\n  sqflite: ^2.3.0"
                    elif dep == "path_provider" and "path_provider:" not in pubspec_content:
                        updated_deps += f"\n  path_provider: ^2.1.1"
                
                # Update pubspec.yaml if changes were made
                if updated_deps != deps_section:
                    pubspec_content = pubspec_content.replace(deps_section, updated_deps)
                    with open(pubspec_path, 'w') as f:
                        f.write(pubspec_content)
                    
                    log_agent_activity("developer", f"Updated dependencies in pubspec.yaml: {dependencies}")
                    return True
        
        elif project_type in ["react", "web"]:
            # For React projects, we would update package.json
            # This is a simplified implementation
            package_json_path = os.path.join(project_dir, "package.json")
            if os.path.exists(package_json_path):
                import json
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                
                # Add dependencies if not already present
                modified = False
                if "dependencies" not in package_json:
                    package_json["dependencies"] = {}
                
                for dep in dependencies:
                    if dep == "axios" and "axios" not in package_json["dependencies"]:
                        package_json["dependencies"]["axios"] = "^1.3.3"
                        modified = True
                    elif dep == "react-router-dom" and "react-router-dom" not in package_json["dependencies"]:
                        package_json["dependencies"]["react-router-dom"] = "^6.8.1"
                        modified = True
                
                # Update package.json if changes were made
                if modified:
                    with open(package_json_path, 'w') as f:
                        json.dump(package_json, f, indent=2)
                    
                    log_agent_activity("developer", f"Updated dependencies in package.json: {dependencies}")
                    return True
        
        return False
        
    except Exception as e:
        log_agent_activity("error_handling", f"Error updating dependencies: {str(e)}")
        return False

def run_flutter_tests(project_dir):
    """Run Flutter tests"""
    try:
        # Check if test directory exists
        if os.path.exists(os.path.join(project_dir, "test")):
            log_agent_activity("testing", "Running Flutter tests")
            
            # Run flutter test
            result = subprocess.run(
                ["flutter", "test"], 
                check=False,  # Don't raise exception on test failure
                cwd=project_dir,
                capture_output=True,
                text=True
            )
            
            # Log test results
            if result.returncode == 0:
                log_agent_activity("testing", "All tests passed!")
            else:
                log_agent_activity("testing", f"Some tests failed: {result.stdout}")
            
            return result.returncode == 0
        else:
            log_agent_activity("testing", "No test directory found")
            return False
            
    except Exception as e:
        log_agent_activity("error_handling", f"Error running tests: {str(e)}")
        return False

def generate_api_docs(project_dir):
    """Generate API documentation for a Flutter project"""
    try:
        log_agent_activity("documentation", "Generating API documentation")
        
        # Create documentation directory
        api_docs_dir = os.path.join(project_dir, "docs", "api")
        os.makedirs(api_docs_dir, exist_ok=True)
        
        # Use dartdoc to generate documentation
        try:
            subprocess.run(
                ["dart", "doc", "--output", api_docs_dir], 
                check=True, 
                cwd=project_dir,
                capture_output=True
            )
            log_agent_activity("documentation", f"Generated API documentation in {api_docs_dir}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: create a simple API documentation markdown file
            models_dir = os.path.join(project_dir, "lib", "models")
            services_dir = os.path.join(project_dir, "lib", "services")
            
            api_doc_content = "# API Documentation\n\n"
            
            # Document models
            if os.path.exists(models_dir):
                api_doc_content += "## Models\n\n"
                
                for model_file in os.listdir(models_dir):
                    if model_file.endswith(".dart"):
                        model_name = os.path.splitext(model_file)[0].replace("_", " ").title()
                        api_doc_content += f"### {model_name}\n\n"
                        api_doc_content += f"File: `lib/models/{model_file}`\n\n"
                        api_doc_content += "**Properties:**\n\n"
                        api_doc_content += "- Properties will vary based on the model\n\n"
            
            # Document services
            if os.path.exists(services_dir):
                api_doc_content += "## Services\n\n"
                
                for service_file in os.listdir(services_dir):
                    if service_file.endswith(".dart"):
                        service_name = os.path.splitext(service_file)[0].replace("_", " ").title()
                        api_doc_content += f"### {service_name}\n\n"
                        api_doc_content += f"File: `lib/services/{service_file}`\n\n"
                        api_doc_content += "**Methods:**\n\n"
                        api_doc_content += "- Methods will vary based on the service\n\n"
            
            # Write the API documentation file
            api_doc_file = os.path.join(api_docs_dir, "api_documentation.md")
            with open(api_doc_file, "w") as f:
                f.write(api_doc_content)
                
            log_agent_activity("documentation", f"Created basic API documentation: {api_doc_file}")
            return True
            
    except Exception as e:
        log_agent_activity("error_handling", f"Error generating API documentation: {str(e)}")
        return False

def customize_ui_components(project_dir, project_type, task):
    """Customize UI components based on project type and task details"""
    try:
        log_agent_activity("ui_ux", f"Customizing UI components for {project_type} project")
        
        if project_type == "flutter":
            # Customize Flutter UI
            # 1. Create theme file
            theme_dir = os.path.join(project_dir, "lib", "theme")
            os.makedirs(theme_dir, exist_ok=True)
            
            theme_file = os.path.join(theme_dir, "app_theme.dart")
            theme_content = """import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData lightTheme = ThemeData(
    primarySwatch: Colors.blue,
    brightness: Brightness.light,
    appBarTheme: const AppBarTheme(
      backgroundColor: Colors.blue,
      foregroundColor: Colors.white,
    ),
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.light,
    ),
    cardTheme: const CardTheme(
      elevation: 2,
      margin: EdgeInsets.all(8),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
  );

  static ThemeData darkTheme = ThemeData(
    primarySwatch: Colors.blue,
    brightness: Brightness.dark,
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.grey[900],
      foregroundColor: Colors.white,
    ),
    colorScheme: ColorScheme.fromSeed(
      seedColor: Colors.blue,
      brightness: Brightness.dark,
    ),
    cardTheme: const CardTheme(
      elevation: 2,
      margin: EdgeInsets.all(8),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
  );
}
"""
            with open(theme_file, "w") as f:
                f.write(theme_content)
                
            log_agent_activity("ui_ux", f"Created app theme: {theme_file}")
            
            # 2. Create custom widgets
            widgets_dir = os.path.join(project_dir, "lib", "widgets")
            os.makedirs(widgets_dir, exist_ok=True)
            
            # Feature widget
            feature_widget_file = os.path.join(widgets_dir, "feature_widget.dart")
            feature_widget_content = """import 'package:flutter/material.dart';

class FeatureCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final VoidCallback? onTap;

  const FeatureCard({
    Key? key,
    required this.title,
    required this.description,
    required this.icon,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, size: 40, color: Theme.of(context).primaryColor),
              const SizedBox(height: 8),
              Text(
                title,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
"""
            with open(feature_widget_file, "w") as f:
                f.write(feature_widget_content)
            
            # Interface widget
            interface_widget_file = os.path.join(widgets_dir, "interface_widget.dart")
            interface_widget_content = """import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;

  const CustomAppBar({
    Key? key,
    required this.title,
    this.actions,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(title),
      actions: actions,
      elevation: 2,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

class CustomButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isPrimary;

  const CustomButton({
    Key? key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isPrimary = true,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final buttonStyle = isPrimary
        ? ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).primaryColor,
            foregroundColor: Colors.white,
          )
        : ElevatedButton.styleFrom(
            backgroundColor: Colors.grey[200],
            foregroundColor: Colors.black87,
          );

    if (icon != null) {
      return ElevatedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon),
        label: Text(label),
        style: buttonStyle,
      );
    }

    return ElevatedButton(
      onPressed: onPressed,
      style: buttonStyle,
      child: Text(label),
    );
  }
}

class CustomTextField extends StatelessWidget {
  final String label;
  final String? hint;
  final TextEditingController? controller;
  final TextInputType keyboardType;
  final bool obscureText;
  final String? Function(String?)? validator;
  final IconData? prefixIcon;

  const CustomTextField({
    Key? key,
    required this.label,
    this.hint,
    this.controller,
    this.keyboardType = TextInputType.text,
    this.obscureText = false,
    this.validator,
    this.prefixIcon,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: keyboardType,
      obscureText: obscureText,
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: prefixIcon != null ? Icon(prefixIcon) : null,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
    );
  }
}
"""
            with open(interface_widget_file, "w") as f:
                f.write(interface_widget_content)
            
            log_agent_activity("ui_ux", f"Created custom widgets in {widgets_dir}")
            
            # 3. Update main.dart to use the theme
            main_dart_path = os.path.join(project_dir, "lib", "main.dart")
            if os.path.exists(main_dart_path):
                with open(main_dart_path, 'r') as f:
                    main_content = f.read()
                
                # Check if we need to add theme import
                if "import 'theme/app_theme.dart'" not in main_content:
                    # Add the theme import
                    import_lines = main_content.split('\n', 10)[:10]
                    for i, line in enumerate(import_lines):
                        if line.startswith('import') and i < len(import_lines) - 1:
                            import_lines.insert(i + 1, "import 'theme/app_theme.dart';")
                            break
                    
                    # Replace the theme in MaterialApp
                    main_content = main_content.replace(
                        "theme: ThemeData(",
                        "theme: AppTheme.lightTheme,\n      darkTheme: AppTheme.darkTheme,"
                    )
                    
                    # Remove the rest of the ThemeData definition if it exists
                    main_content = re.sub(
                        r'theme: ThemeData\([^)]+\),', 
                        'theme: AppTheme.lightTheme,', 
                        main_content
                    )
                    
                    with open(main_dart_path, 'w') as f:
                        f.write(main_content)
                    
                    log_agent_activity("ui_ux", "Updated main.dart to use the app theme")
        
        elif project_type in ["react", "web"]:
            # Customize React UI
            # This is a simplified implementation
            log_agent_activity("ui_ux", "Creating custom React UI components")
            
            components_dir = os.path.join(project_dir, "src", "components")
            os.makedirs(components_dir, exist_ok=True)
            
            # Create a UI component file
            ui_component_file = os.path.join(components_dir, "UIComponents.js")
            ui_component_content = """import React from 'react';

// Button component
export const Button = ({ 
  children, 
  onClick, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false 
}) => {
  // Define style classes based on props
  const baseClass = 'btn';
  const variantClass = `btn-${variant}`;
  const sizeClass = `btn-${size}`;
  const className = [baseClass, variantClass, sizeClass, disabled ? 'btn-disabled' : ''].join(' ');
  
  return (
    <button 
      className={className}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

// Card component
export const Card = ({ 
  children, 
  title,
  subtitle,
  className = '',
  footer
}) => {
  return (
    <div className={`card ${className}`}>
      {title && (
        <div className="card-header">
          <h3 className="card-title">{title}</h3>
          {subtitle && <div className="card-subtitle">{subtitle}</div>}
        </div>
      )}
      <div className="card-body">
        {children}
      </div>
      {footer && (
        <div className="card-footer">
          {footer}
        </div>
      )}
    </div>
  );
};

// Form Input component
export const Input = ({
  label,
  type = 'text',
  id,
  name,
  value,
  onChange,
  placeholder,
  error,
  required = false
}) => {
  return (
    <div className="form-group">
      {label && (
        <label htmlFor={id} className="form-label">
          {label} {required && <span className="required">*</span>}
        </label>
      )}
      <input
        type={type}
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`form-input ${error ? 'has-error' : ''}`}
        required={required}
      />
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

// Navigation component
export const Navigation = ({ links = [] }) => {
  return (
    <nav className="navigation">
      <ul className="nav-list">
        {links.map((link, index) => (
          <li key={index} className="nav-item">
            <a href={link.url} className="nav-link">
              {link.icon && <span className="nav-icon">{link.icon}</span>}
              <span className="nav-text">{link.text}</span>
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};
"""
            with open(ui_component_file, "w") as f:
                f.write(ui_component_content)
            
            # Create a styles file
            styles_dir = os.path.join(project_dir, "src", "styles")
            os.makedirs(styles_dir, exist_ok=True)
            
            styles_file = os.path.join(styles_dir, "theme.css")
            styles_content = """/* Main Theme Variables */
:root {
  --primary-color: #3498db;
  --secondary-color: #2ecc71;
  --accent-color: #9b59b6;
  --text-color: #333333;
  --background-color: #ffffff;
  --error-color: #e74c3c;
  --success-color: #2ecc71;
  --warning-color: #f39c12;
  --light-gray: #f5f5f5;
  --medium-gray: #e0e0e0;
  --dark-gray: #9e9e9e;
  
  /* Spacing variables */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Font sizes */
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-xxl: 2rem;
  
  /* Border radius */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.5rem;
  --border-radius-lg: 1rem;
  --border-radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 0.15s ease;
  --transition-normal: 0.3s ease;
  --transition-slow: 0.5s ease;
}

/* Button Styles */
.btn {
  display: inline-block;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
  user-select: none;
  border: 1px solid transparent;
  padding: 0.5rem 1rem;
  font-size: var(--font-size-md);
  line-height: 1.5;
  border-radius: var(--border-radius-md);
  transition: all var(--transition-normal);
  cursor: pointer;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-secondary:hover {
  background-color: #27ae60;
}

.btn-small {
  padding: 0.25rem 0.5rem;
  font-size: var(--font-size-sm);
}

.btn-medium {
  padding: 0.5rem 1rem;
  font-size: var(--font-size-md);
}

.btn-large {
  padding: 0.75rem 1.5rem;
  font-size: var(--font-size-lg);
}

.btn-disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

/* Card Styles */
.card {
  background-color: var(--background-color);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-md);
  overflow: hidden;
  margin-bottom: var(--spacing-md);
}

.card-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--medium-gray);
}

.card-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: 500;
}

.card-subtitle {
  color: var(--dark-gray);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-xs);
}

.card-body {
  padding: var(--spacing-md);
}

.card-footer {
  padding: var(--spacing-md);
  border-top: 1px solid var(--medium-gray);
  background-color: var(--light-gray);
}

/* Form Styles */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
}

.form-input {
  display: block;
  width: 100%;
  padding: 0.5rem 0.75rem;
  font-size: var(--font-size-md);
  line-height: 1.5;
  color: var(--text-color);
  background-color: var(--background-color);
  background-clip: padding-box;
  border: 1px solid var(--medium-gray);
  border-radius: var(--border-radius-md);
  transition: border-color var(--transition-normal);
}

.form-input:focus {
  border-color: var(--primary-color);
  outline: 0;
}

.form-input.has-error {
  border-color: var(--error-color);
}

.error-message {
  color: var(--error-color);
  font-size: var(--font-size-sm);
  margin-top: var(--spacing-xs);
}

.required {
  color: var(--error-color);
}

/* Navigation Styles */
.navigation {
  background-color: var(--background-color);
  box-shadow: var(--shadow-sm);
}

.nav-list {
  display: flex;
  list-style-type: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  margin-right: var(--spacing-md);
}

.nav-link {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  color: var(--text-color);
  text-decoration: none;
  transition: color var(--transition-normal);
}

.nav-link:hover {
  color: var(--primary-color);
}

.nav-icon {
  margin-right: var(--spacing-xs);
}
"""
            with open(styles_file, "w") as f:
                f.write(styles_content)
            
            # Update index.js to import the theme
            index_js_path = os.path.join(project_dir, "src", "index.js")
            if os.path.exists(index_js_path):
                with open(index_js_path, 'r') as f:
                    index_content = f.read()
                
                # Add theme import if not exists
                if "import './styles/theme.css';" not in index_content:
                    index_content = index_content.replace(
                        "import './index.css';",
                        "import './index.css';\nimport './styles/theme.css';"
                    )
                    
                    with open(index_js_path, 'w') as f:
                        f.write(index_content)
            
            log_agent_activity("ui_ux", "Created React UI components and theme")
        
        return True
        
    except Exception as e:
        log_agent_activity("error_handling", f"Error customizing UI components: {str(e)}")
        return False

def add_flutter_error_handling(project_dir):
    """Add error handling to a Flutter project"""
    try:
        # Create error handling directory
        utils_dir = os.path.join(project_dir, "lib", "utils")
        os.makedirs(utils_dir, exist_ok=True)
        
        # Create error handler file
        error_handler_file = os.path.join(utils_dir, "error_handler.dart")
        error_handler_content = """import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';

class ErrorHandler {
  // Singleton instance
  static final ErrorHandler _instance = ErrorHandler._internal();
  factory ErrorHandler() => _instance;
  ErrorHandler._internal();

  // Error handling methods
  void handleError(BuildContext context, dynamic error, {String? customMessage}) {
    String message = customMessage ?? 'An error occurred';
    
    if (error is SocketException) {
      message = 'Network error: Unable to connect to the server';
    } else if (error is TimeoutException) {
      message = 'Connection timeout: Please try again later';
    } else if (error is FormatException) {
      message = 'Data format error: Please contact support';
    }
    
    _showErrorSnackBar(context, message);
    
    // Log the error (you could integrate with a logging service here)
    debugPrint('ERROR: ${error.toString()}');
  }
  
  void _showErrorSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red[700],
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: 'Dismiss',
          textColor: Colors.white,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }
  
  // Widget for error states in the UI
  Widget errorWidget(String message, {VoidCallback? onRetry}) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            color: Colors.red,
            size: 60,
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(fontSize: 16),
            textAlign: TextAlign.center,
          ),
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
          ],
        ],
      ),
    );
  }
}

// Extension for try-catch simplification
extension FutureExtensions<T> on Future<T> {
  Future<T> handleError(BuildContext context, {String? customMessage}) async {
    try {
      return await this;
    } catch (e) {
      ErrorHandler().handleError(context, e, customMessage: customMessage);
      rethrow;
    }
  }
}
"""
        with open(error_handler_file, "w") as f:
            f.write(error_handler_content)
            
        log_agent_activity("error_handling", f"Created error handler: {error_handler_file}")
        
        return True
        
    except Exception as e:
        log_agent_activity("error_handling", f"Error creating error handling: {str(e)}")
        return False

def add_react_error_handling(project_dir):
    """Add error handling to a React project"""
    try:
        # Create error handling directory
        utils_dir = os.path.join(project_dir, "src", "utils")
        os.makedirs(utils_dir, exist_ok=True)
        
        # Create error handler file
        error_handler_file = os.path.join(utils_dir, "ErrorHandler.js")
        error_handler_content = """import React from 'react';

// Error boundary component
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to an error reporting service
    console.error("Error caught by error boundary:", error, errorInfo);
    this.setState({ error, errorInfo });
    
    // You could send to a monitoring service here
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <p>The application encountered an error. Please try again later.</p>
          {this.props.showReset && (
            <button 
              onClick={() => this.setState({ hasError: false, error: null, errorInfo: null })}
              className="btn btn-primary"
            >
              Try again
            </button>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

// Error message component
export const ErrorMessage = ({ message, onRetry }) => (
  <div className="error-message-container">
    <div className="error-icon">⚠️</div>
    <p className="error-text">{message || 'An error occurred'}</p>
    {onRetry && (
      <button onClick={onRetry} className="btn btn-sm btn-primary">
        Retry
      </button>
    )}
  </div>
);

// API error handler utility
export const handleApiError = (error) => {
  let errorMessage = 'An unexpected error occurred';
  
  if (!error.response) {
    // Network error
    errorMessage = 'Network error - please check your connection';
  } else {
    // HTTP error response
    const status = error.response.status;
    
    switch (status) {
      case 400:
        errorMessage = 'Bad request - please check your input';
        break;
      case 401:
        errorMessage = 'Unauthorized - please login again';
        break;
      case 403:
        errorMessage = 'Forbidden - you do not have permission to access this resource';
        break;
      case 404:
        errorMessage = 'Resource not found';
        break;
      case 500:
        errorMessage = 'Server error - please try again later';
        break;
      default:
        errorMessage = `Error ${status} - please try again`;
    }
  }
  
  return { 
    message: errorMessage,
    originalError: error
  };
};

// Custom hook for API calls with error handling
export const useApiWithErrorHandling = (apiFunction) => {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [data, setData] = React.useState(null);
  
  const execute = async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunction(...args);
      setData(result);
      return result;
    } catch (error) {
      const handledError = handleApiError(error);
      setError(handledError);
      throw handledError;
    } finally {
      setLoading(false);
    }
  };
  
  return { execute, loading, error, data };
};

// Global error handler for unexpected errors
export const setupGlobalErrorHandler = () => {
  window.addEventListener('error', (event) => {
    console.error('Global error handler caught:', event.error);
    // You could send to a monitoring service here
    // logErrorToService(event.error);
    
    // Optional: Show a user-friendly message
    // showErrorToast('An unexpected error occurred');
  });
  
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // You could send to a monitoring service here
    // logErrorToService(event.reason);
  });
};
"""
        with open(error_handler_file, "w") as f:
            f.write(error_handler_content)
            
        # Create error handling CSS
        error_styles_file = os.path.join(utils_dir, "error-styles.css")
        error_styles_content = """.error-boundary {
  text-align: center;
  padding: 2rem;
  margin: 1rem;
  border: 1px solid #f5c6cb;
  border-radius: 0.25rem;
  background-color: #f8d7da;
  color: #721c24;
}

.error-message-container {
  display: flex;
  align-items: center;
  padding: 0.75rem 1.25rem;
  margin-bottom: 1rem;
  border: 1px solid #f5c6cb;
  border-radius: 0.25rem;
  background-color: #f8d7da;
  color: #721c24;
}

.error-icon {
  font-size: 1.5rem;
  margin-right: 0.75rem;
}

.error-text {
  margin: 0;
  flex-grow: 1;
}
"""
        with open(error_styles_file, "w") as f:
            f.write(error_styles_content)
            
        # Update App.js to use error boundary if it exists
        app_js_path = os.path.join(project_dir, "src", "App.js")
        if os.path.exists(app_js_path):
            with open(app_js_path, 'r') as f:
                app_content = f.read()
            
            # Add error boundary imports and usage if not already present
            if "import { ErrorBoundary } from './utils/ErrorHandler'" not in app_content:
                # Add import
                app_content = app_content.replace(
                    "import React from 'react';", 
                    "import React from 'react';\nimport { ErrorBoundary } from './utils/ErrorHandler';\nimport './utils/error-styles.css';"
                )
                
                # Wrap the app content in error boundary
                app_content = app_content.replace(
                    "<div className=\"app\">",
                    "<ErrorBoundary showReset={true}>\n      <div className=\"app\">"
                )
                
                app_content = app_content.replace(
                    "  </div>",
                    "  </div>\n    </ErrorBoundary>"
                )
                
                with open(app_js_path, 'w') as f:
                    f.write(app_content)
            
        # Update index.js to setup global error handler
        index_js_path = os.path.join(project_dir, "src", "index.js")
        if os.path.exists(index_js_path):
            with open(index_js_path, 'r') as f:
                index_content = f.read()
            
            # Add error handler setup if not already present
            if "setupGlobalErrorHandler" not in index_content:
                index_content = index_content.replace(
                    "import App from './App';", 
                    "import App from './App';\nimport { setupGlobalErrorHandler } from './utils/ErrorHandler';"
                )
                
                # Add the setup call
                if "ReactDOM.createRoot" in index_content:
                    # For React 18
                    index_content = index_content.replace(
                        "const root = ReactDOM.createRoot(document.getElementById('root'));", 
                        "// Setup global error handler\nsetupGlobalErrorHandler();\n\nconst root = ReactDOM.createRoot(document.getElementById('root'));"
                    )
                else:
                    # For older React versions
                    index_content = index_content.replace(
                        "ReactDOM.render(", 
                        "// Setup global error handler\nsetupGlobalErrorHandler();\n\nReactDOM.render("
                    )
                
                with open(index_js_path, 'w') as f:
                    f.write(index_content)
            
        log_agent_activity("error_handling", "Added React error handling components and utilities")
        
        return True
        
    except Exception as e:
        log_agent_activity("error_handling", f"Error creating React error handling: {str(e)}")
        return False

def integrate_react_components(project_dir, task):
    """Integrate React components based on task requirements"""
    try:
        log_agent_activity("integration", "Integrating React components")
        
        # Create services directory if it doesn't exist
        services_dir = os.path.join(project_dir, "src", "services")
        os.makedirs(services_dir, exist_ok=True)
        
        # Create API service
        api_service_file = os.path.join(services_dir, "api.js")
        api_service_content = """import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'https://api.example.com',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // Handle specific error cases
    if (error.response) {
      // Server responded with a status code outside of 2xx range
      if (error.response.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

// API methods for various resources
export const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  logout: () => {
    localStorage.removeItem('token');
    return Promise.resolve();
  },
  getCurrentUser: () => api.get('/auth/user'),
};

export const userService = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
};

// Add more services as needed for your application
export const productService = {
  getProducts: () => api.get('/products'),
  getProduct: (id) => api.get(`/products/${id}`),
  createProduct: (data) => api.post('/products', data),
  updateProduct: (id, data) => api.put(`/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/products/${id}`),
};
"""
        with open(api_service_file, "w") as f:
            f.write(api_service_content)
        
        # Create a local storage service
        storage_service_file = os.path.join(services_dir, "storage.js")
        storage_service_content = """// Local storage service for persisting data

const storagePrefix = 'app_';

const storage = {
  // Get a value from local storage by key
  getItem: (key) => {
    try {
      return JSON.parse(window.localStorage.getItem(`${storagePrefix}${key}`));
    } catch (error) {
      console.error(`Error getting item ${key} from localStorage:`, error);
      return null;
    }
  },
  
  // Set a value in local storage
  setItem: (key, value) => {
    try {
      window.localStorage.setItem(`${storagePrefix}${key}`, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting item ${key} in localStorage:`, error);
    }
  },
  
  // Remove an item from local storage
  removeItem: (key) => {
    try {
      window.localStorage.removeItem(`${storagePrefix}${key}`);
    } catch (error) {
      console.error(`Error removing item ${key} from localStorage:`, error);
    }
  },
  
  // Clear all app-specific items from local storage
  clear: () => {
    try {
      Object.keys(window.localStorage)
        .filter(key => key.startsWith(storagePrefix))
        .forEach(key => window.localStorage.removeItem(key));
    } catch (error) {
      console.error('Error clearing localStorage:', error);
    }
  },
};

export default storage;
"""
        with open(storage_service_file, "w") as f:
            f.write(storage_service_content)
        
        # Create authentication context
        context_dir = os.path.join(project_dir, "src", "context")
        os.makedirs(context_dir, exist_ok=True)
        
        auth_context_file = os.path.join(context_dir, "AuthContext.js")
        auth_context_content = """import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';
import storage from '../services/storage';

// Create context
const AuthContext = createContext(null);

// Auth provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user on initial render
  useEffect(() => {
    const loadUser = async () => {
      const token = storage.getItem('token');
      
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error('Error loading user', err);
          storage.removeItem('token');
        }
      }
      
      setLoading(false);
    };
    
    loadUser();
  }, []);

  // Login function
  const login = async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authService.login(credentials);
      
      // Store token and user info
      storage.setItem('token', response.token);
      setUser(response.user);
      
      return response.user;
    } catch (err) {
      setError(err.message || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authService.register(userData);
      
      // Store token and user info
      storage.setItem('token', response.token);
      setUser(response.user);
      
      return response.user;
    } catch (err) {
      setError(err.message || 'Registration failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
      storage.removeItem('token');
      setUser(null);
    } catch (err) {
      console.error('Logout error', err);
    }
  };

  // Update user function
  const updateUser = (userData) => {
    setUser(userData);
  };

  // Create context value
  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Custom hook for using auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};
"""
        with open(auth_context_file, "w") as f:
            f.write(auth_context_content)
        
        # Create app context for global state
        app_context_file = os.path.join(context_dir, "AppContext.js")
        app_context_content = """import React, { createContext, useContext, useReducer } from 'react';

// Initial state
const initialState = {
  theme: 'light',
  notifications: [],
  appLoading: false,
};

// Action types
const ActionTypes = {
  SET_THEME: 'SET_THEME',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  SET_LOADING: 'SET_LOADING',
};

// Reducer function
const appReducer = (state, action) => {
  switch (action.type) {
    case ActionTypes.SET_THEME:
      return {
        ...state,
        theme: action.payload,
      };
    case ActionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };
    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(
          (notif) => notif.id !== action.payload
        ),
      };
    case ActionTypes.SET_LOADING:
      return {
        ...state,
        appLoading: action.payload,
      };
    default:
      return state;
  }
};

// Create context
const AppContext = createContext(null);

// App provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Create actions
  const setTheme = (theme) => {
    dispatch({ type: ActionTypes.SET_THEME, payload: theme });
  };

  const addNotification = (notification) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification = { id, ...notification };
    
    dispatch({ 
      type: ActionTypes.ADD_NOTIFICATION, 
      payload: newNotification,
    });
    
    // Auto remove after timeout if specified
    if (notification.timeout) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.timeout);
    }
    
    return id;
  };

  const removeNotification = (id) => {
    dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: id });
  };

  const setLoading = (isLoading) => {
    dispatch({ type: ActionTypes.SET_LOADING, payload: isLoading });
  };

  // Create context value
  const value = {
    ...state,
    setTheme,
    addNotification,
    removeNotification,
    setLoading,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook for using app context
export const useApp = () => {
  const context = useContext(AppContext);
  
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  
  return context;
};
"""
        with open(app_context_file, "w") as f:
            f.write(app_context_content)
        
        # Update App.js to use contexts if it exists
        app_js_path = os.path.join(project_dir, "src", "App.js")
        if os.path.exists(app_js_path):
            with open(app_js_path, 'r') as f:
                app_content = f.read()
            
            # Add context providers if not already present
            if "AppProvider" not in app_content and "AuthProvider" not in app_content:
                # Add imports
                app_content = app_content.replace(
                    "import { Routes, Route } from 'react-router-dom';", 
                    "import { Routes, Route } from 'react-router-dom';\nimport { AppProvider } from './context/AppContext';\nimport { AuthProvider } from './context/AuthContext';"
                )
                
                # Wrap the app with providers
                app_content = app_content.replace(
                    "function App() {", 
                    "function App() {"
                )
                
                app_content = app_content.replace(
                    "return (", 
                    "return (\n    <AppProvider>\n      <AuthProvider>"
                )
                
                app_content = app_content.replace(
                    "  );", 
                    "      </AuthProvider>\n    </AppProvider>\n  );"
                )
                
                with open(app_js_path, 'w') as f:
                    f.write(app_content)
        
        log_agent_activity("integration", "Integrated React components and services")
        
        return True
        
    except Exception as e:
        log_agent_activity("error_handling", f"Error integrating React components: {str(e)}")
        return False