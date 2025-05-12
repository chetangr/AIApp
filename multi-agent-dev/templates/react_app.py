import os
import re
from typing import Dict, Any, List

# Import required utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log_agent_activity

def create_react_app(task, app_name, project_dir):
    """Create a React web application based on task requirements"""
    log_agent_activity("developer", f"Creating React app: {app_name}")
    
    # Extract key information from the task
    title = task.get("title", "")
    description = task.get("description", "")
    
    # Parse task description for keywords to determine app type and features
    content = (title + " " + description).lower()
    
    # Detect app type and main features
    app_type = "generic"
    app_features = []
    
    # E-commerce detection
    if any(word in content for word in ["shop", "store", "ecommerce", "product", "cart"]):
        app_type = "ecommerce"
        app_features = ["product_listing", "shopping_cart", "checkout"]
        
    # Blog/CMS detection
    elif any(word in content for word in ["blog", "cms", "content", "post", "article"]):
        app_type = "blog"
        app_features = ["post_listing", "post_detail", "categories"]
        
    # Dashboard detection
    elif any(word in content for word in ["dashboard", "admin", "analytics", "monitor"]):
        app_type = "dashboard"
        app_features = ["data_visualization", "user_management", "reports"]
        
    # Social media detection
    elif any(word in content for word in ["social", "friend", "network", "feed"]):
        app_type = "social"
        app_features = ["user_profiles", "feed", "messaging"]
    
    # Learning platform detection
    elif any(word in content for word in ["learn", "course", "education", "lesson"]):
        app_type = "learning"
        app_features = ["course_listing", "lessons", "progress_tracking"]
    
    # Ensure we have at least some features
    if not app_features:
        app_features = ["homepage", "about", "contact"]
    
    # Always add authentication if it seems needed
    if any(word in content for word in ["login", "user", "account", "profile", "auth"]):
        if "authentication" not in app_features:
            app_features.append("authentication")
    
    # Create the directory structure
    os.makedirs(os.path.join(project_dir, "public"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "components"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "pages"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "services"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "hooks"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "context"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "src", "assets"), exist_ok=True)
    
    # Determine which pages to create based on app type and features
    pages = ["Home"]
    if app_type == "ecommerce":
        pages.extend(["Products", "ProductDetail", "Cart", "Checkout"])
    elif app_type == "blog":
        pages.extend(["Posts", "PostDetail", "Categories"])
    elif app_type == "dashboard":
        pages.extend(["Dashboard", "Analytics", "Users", "Reports"])
    elif app_type == "social":
        pages.extend(["Feed", "Profile", "Messages"])
    elif app_type == "learning":
        pages.extend(["Courses", "CourseDetail", "Lesson", "Progress"])
    
    # Add authentication pages if needed
    if "authentication" in app_features:
        pages.extend(["Login", "Register", "Profile"])
    
    # Create package.json
    display_name = ' '.join(word.capitalize() for word in app_name.replace('_', ' ').split())
    
    # Define dependencies based on app type and features
    dependencies = {
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-router-dom": "^6.8.1",
        "axios": "^1.3.3"
    }
    
    # Add feature-specific dependencies
    if app_type == "dashboard" or "data_visualization" in app_features:
        dependencies["recharts"] = "^2.4.3"
    
    if "authentication" in app_features:
        dependencies["jwt-decode"] = "^3.1.2"
    
    if app_type == "ecommerce":
        dependencies["react-use-cart"] = "^1.13.0"
    
    # Create the dependencies string
    deps_str = ",\n    ".join([f'"{k}": "{v}"' for k, v in dependencies.items()])
    
    package_json = f"""{{
  "name": "{app_name}",
  "version": "0.1.0",
  "private": true,
  "dependencies": {{
    {deps_str}
  }},
  "scripts": {{
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }},
  "eslintConfig": {{
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  }},
  "browserslist": {{
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }}
}}
"""
    
    with open(os.path.join(project_dir, "package.json"), "w") as f:
        f.write(package_json)
    
    # Create index.html
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="{task.get('description', 'Web application created by Multi-Agent Dev')}"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>{display_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""
    
    with open(os.path.join(project_dir, "public", "index.html"), "w") as f:
        f.write(index_html)
    
    # Create manifest.json
    manifest_json = f"""{{
  "short_name": "{display_name}",
  "name": "{display_name}",
  "icons": [
    {{
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }}
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}}
"""
    
    with open(os.path.join(project_dir, "public", "manifest.json"), "w") as f:
        f.write(manifest_json)
    
    # Create index.js
    index_js = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { BrowserRouter } from 'react-router-dom';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
"""
    
    with open(os.path.join(project_dir, "src", "index.js"), "w") as f:
        f.write(index_js)
    
    # Create index.css
    index_css = """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.header {
  background-color: #282c34;
  padding: 1rem;
  color: white;
}

.footer {
  background-color: #282c34;
  padding: 1rem;
  color: white;
  text-align: center;
  margin-top: 2rem;
}

.nav-links {
  display: flex;
  list-style: none;
  padding: 0;
}

.nav-links li {
  margin-right: 1rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
}

.nav-links a:hover {
  text-decoration: underline;
}

.btn {
  padding: 0.5rem 1rem;
  background-color: #61dafb;
  color: #282c34;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.btn:hover {
  background-color: #4fa8cc;
}
"""
    
    with open(os.path.join(project_dir, "src", "index.css"), "w") as f:
        f.write(index_css)
    
    # Create App.js with routes
    routes = []
    imports = []
    
    for page in pages:
        page_path = page if page != "Home" else ""
        routes.append(f'        <Route path="/{page_path.lower()}" element={{<{page}Page />}} />')
        imports.append(f'import {page}Page from "./pages/{page}";')
    
    app_js = f"""import {{ Routes, Route }} from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
{chr(10).join(imports)}

function App() {{
  return (
    <div className="app">
      <Header />
      <main className="container">
        <Routes>
{chr(10).join(routes)}
        </Routes>
      </main>
      <Footer />
    </div>
  );
}}

export default App;
"""
    
    with open(os.path.join(project_dir, "src", "App.js"), "w") as f:
        f.write(app_js)
    
    # Create Header component
    nav_links = []
    for page in pages:
        page_name = page
        page_path = page.lower() if page != "Home" else ""
        nav_links.append(f'          <li><a href="/{page_path}">{page_name}</a></li>')
    
    header_js = f"""import React from 'react';

function Header() {{
  return (
    <header className="header">
      <div className="container">
        <h1>{display_name}</h1>
        <nav>
          <ul className="nav-links">
{chr(10).join(nav_links)}
          </ul>
        </nav>
      </div>
    </header>
  );
}}

export default Header;
"""
    
    with open(os.path.join(project_dir, "src", "components", "Header.js"), "w") as f:
        f.write(header_js)
    
    # Create Footer component
    footer_js = f"""import React from 'react';

function Footer() {{
  return (
    <footer className="footer">
      <div className="container">
        <p>&copy; {display_name} {2023} - All Rights Reserved</p>
      </div>
    </footer>
  );
}}

export default Footer;
"""
    
    with open(os.path.join(project_dir, "src", "components", "Footer.js"), "w") as f:
        f.write(footer_js)
    
    # Create page components for each page
    for page in pages:
        page_content = f"""import React from 'react';

function {page}Page() {{
  return (
    <div>
      <h2>{page} Page</h2>
      <p>This is the {page.lower()} page content.</p>
    </div>
  );
}}

export default {page}Page;
"""
        
        with open(os.path.join(project_dir, "src", "pages", f"{page}.js"), "w") as f:
            f.write(page_content)
    
    # Create README.md
    readme_content = f"""# {display_name}

{task.get("description", "A React application")}

## Features

{chr(10).join(["- " + feature.replace("_", " ").title() for feature in app_features])}

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone this repository
2. Navigate to the project directory
3. Run `npm install` to install dependencies
4. Run `npm start` to start the development server

## Project Structure

- `public/`: Static files and HTML template
- `src/`: React components and application code
  - `components/`: Reusable UI components
  - `pages/`: Page components
  - `services/`: API and service files
  - `hooks/`: Custom React hooks
  - `context/`: React context providers
  - `assets/`: Images, icons, and other static assets

## Available Scripts

- `npm start`: Runs the app in development mode
- `npm test`: Launches the test runner
- `npm run build`: Builds the app for production

## Learn More

To learn more about React, check out the [React documentation](https://reactjs.org/).
"""
    
    with open(os.path.join(project_dir, "README.md"), "w") as f:
        f.write(readme_content)
    
    log_agent_activity("developer", f"Created React app: {app_name}")
    
    return True