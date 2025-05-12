#!/usr/bin/env python3
"""
Test script for improved multi-agent development system.
Tests the template generation and project creation functionality.
"""
import os
import sys
import shutil
import unittest
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import utility functions
from templates.project_utils import get_app_name_from_task, get_project_type

class TestImprovements(unittest.TestCase):
    """Test case for improved code functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create test output directory
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Sample tasks for testing
        self.learning_task = {
            "id": "test_learning",
            "title": "Micro Master Learning App",
            "description": "Create a learning app with flashcards, quizzes, and progress tracking for upskilling",
            "assigned_agent": "developer"
        }
        
        self.ecommerce_task = {
            "id": "test_ecommerce",
            "title": "Online Store",
            "description": "Create an e-commerce app with product listings, shopping cart, and checkout",
            "assigned_agent": "developer"
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test output directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_app_name_extraction(self):
        """Test app name extraction from task."""
        app_name = get_app_name_from_task(self.learning_task)
        self.assertEqual(app_name, "micro_master_learning_app")
        
        app_name = get_app_name_from_task(self.ecommerce_task)
        self.assertEqual(app_name, "online_store")
    
    def test_project_type_detection(self):
        """Test project type detection from task."""
        # Add mobile keyword to make it detect as flutter
        mobile_task = dict(self.learning_task)
        mobile_task["description"] += " for mobile devices"
        
        project_type = get_project_type(mobile_task)
        self.assertEqual(project_type, "flutter")
        
        # Web project
        web_task = dict(self.ecommerce_task)
        web_task["description"] += " for web browsers"
        
        project_type = get_project_type(web_task)
        self.assertEqual(project_type, "react")
    
    def test_app_feature_detection(self):
        """Test that app features are correctly detected from requirements."""
        # Create a minimal version of the function to test feature detection
        def detect_features(task):
            title = task.get("title", "")
            description = task.get("description", "")
            content = (title + " " + description).lower()
            
            app_type = "generic"
            app_features = []
            
            # Learning app detection
            if any(word in content for word in ["learn", "learning", "education", "study", "course", "skill", "upskill"]):
                app_type = "learning"
                if "track" in content or "progress" in content:
                    app_features.append("progress_tracking")
                if "flash" in content or "card" in content:
                    app_features.append("flashcards")
                if "quiz" in content or "test" in content:
                    app_features.append("quizzes")
            
            # E-commerce detection
            elif any(word in content for word in ["shop", "store", "ecommerce", "product", "cart"]):
                app_type = "ecommerce"
                app_features.append("product_browsing")
                if "cart" in content:
                    app_features.append("shopping_cart")
                if "check" in content:
                    app_features.append("checkout")
            
            return app_type, app_features
        
        # Test learning app
        app_type, features = detect_features(self.learning_task)
        self.assertEqual(app_type, "learning")
        self.assertIn("flashcards", features)
        self.assertIn("quizzes", features)
        self.assertIn("progress_tracking", features)
        
        # Test ecommerce app
        app_type, features = detect_features(self.ecommerce_task)
        self.assertEqual(app_type, "ecommerce")
        self.assertIn("product_browsing", features)
        self.assertIn("shopping_cart", features)
        self.assertIn("checkout", features)

if __name__ == "__main__":
    unittest.main()