#!/usr/bin/env python3
"""
Simple script to install dependencies for the Multi-Agent Development System
"""
import sys
import subprocess
import importlib.util

def check_dependency(name):
    """Check if a Python package is installed"""
    return importlib.util.find_spec(name) is not None

def install_dependency(name):
    """Install a Python package using pip"""
    print(f"Installing {name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", name])
    print(f"Successfully installed {name}")

def main():
    """Main function to check and install dependencies"""
    # List of dependencies to check/install
    dependencies = {
        "anthropic": "anthropic",
        "python-dotenv": "dotenv"
    }
    
    missing = []
    
    # Check which dependencies are missing
    for package, module in dependencies.items():
        if not check_dependency(module):
            missing.append(package)
    
    if not missing:
        print("All dependencies are already installed!")
        return
    
    print(f"Found {len(missing)} missing dependencies: {', '.join(missing)}")
    print("Installing missing dependencies...")
    
    # Install missing dependencies
    for package in missing:
        install_dependency(package)
    
    print("\nAll dependencies installed successfully!")
    print("You can now run the application with: streamlit run app.py")

if __name__ == "__main__":
    main()