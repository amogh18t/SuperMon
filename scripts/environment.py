#!/usr/bin/env python3
"""
Environment management for SuperMon.
"""

import os
import sys
import subprocess
from typing import Dict, List, Optional

from scripts.utils import (
    print_status, print_success, print_warning, print_error,
    run_command, get_project_root, check_conda
)


def setup_conda_env() -> bool:
    """Set up the conda environment."""
    print_status("Setting up conda environment...")
    
    if not check_conda():
        print_error("Conda is not installed. Please install Miniconda or Anaconda first.")
        print_error("Download from: https://docs.conda.io/en/latest/miniconda.html")
        return False
    
    project_root = get_project_root()
    env_file = os.path.join(project_root, "environment.yml")
    
    if not os.path.exists(env_file):
        print_error(f"Environment file not found: {env_file}")
        return False
    
    # Check if environment exists
    try:
        result = run_command(["conda", "env", "list"])
        if "supermon" in result.stdout:
            print_status("Conda environment 'supermon' already exists")
        else:
            print_status("Creating conda environment from environment.yml...")
            run_command(["conda", "env", "create", "-f", env_file])
            print_success("Conda environment created")
    except subprocess.CalledProcessError:
        print_error("Failed to set up conda environment")
        return False
    
    return True


def setup_frontend_deps() -> bool:
    """Set up frontend dependencies."""
    print_status("Setting up frontend dependencies...")
    
    project_root = get_project_root()
    frontend_dir = os.path.join(project_root, "frontend")
    node_modules = os.path.join(frontend_dir, "node_modules")
    
    if not os.path.exists(frontend_dir):
        print_error(f"Frontend directory not found: {frontend_dir}")
        return False
    
    if os.path.exists(node_modules):
        print_status("Frontend dependencies already installed")
        return True
    
    try:
        run_command(["npm", "install"], cwd=frontend_dir)
        print_success("Frontend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install frontend dependencies")
        return False


def check_env_file() -> bool:
    """Check if .env file exists, create from template if not."""
    print_status("Checking environment variables...")
    
    project_root = get_project_root()
    env_file = os.path.join(project_root, ".env")
    env_example = os.path.join(project_root, ".env.example")
    
    if os.path.exists(env_file):
        print_success("Environment file found")
        return True
    
    print_warning("No .env file found. Creating from template...")
    
    # If .env.example exists, copy it to .env
    if os.path.exists(env_example):
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
    else:
        # Create default .env file
        with open(env_file, 'w') as f:
            f.write("""# AI Services
            GEMINI_API_KEY=your_gemini_api_key_here
            OPENAI_API_KEY=your_openai_api_key_here

            # Communication Services
            SLACK_BOT_TOKEN=your_slack_bot_token_here
            WHATSAPP_API_KEY=your_whatsapp_api_key_here
            WEBEX_ACCESS_TOKEN=your_webex_token_here

            # Project Management
            NOTION_API_KEY=your_notion_api_key_here
            GITHUB_TOKEN=your_github_token_here

            # Database
            DATABASE_URL=postgresql://supermon:supermon123@localhost/supermon
            REDIS_URL=redis://localhost:6379

            # Frontend
            NEXT_PUBLIC_API_URL=http://localhost:8000
            """)
    
    print_warning("Please update .env file with your API keys before starting services")
    return True


def run_code_quality_checks() -> bool:
    """Run code quality checks."""
    print_status("Running code quality checks...")
    
    project_root = get_project_root()
    pre_commit_config = os.path.join(project_root, ".pre-commit-config.yaml")
    
    if not os.path.exists(pre_commit_config):
        print_warning("Pre-commit config not found, skipping code quality checks")
        return True
    
    try:
        # Install pre-commit hooks
        run_command(["pre-commit", "install"], cwd=project_root)
        
        # Run all hooks
        run_command(["pre-commit", "run", "--all-files"], cwd=project_root)
        
        print_success("Code quality checks completed")
        return True
    except subprocess.CalledProcessError:
        print_error("Code quality checks failed")
        return False


def format_code() -> bool:
    """Format code using black and isort."""
    print_status("Formatting code...")
    
    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")
    
    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False
    
    try:
        # Run black
        run_command(["black", "."], cwd=backend_dir)
        
        # Run isort
        run_command(["isort", "."], cwd=backend_dir)
        
        print_success("Code formatting completed")
        return True
    except subprocess.CalledProcessError:
        print_error("Code formatting failed")
        return False


def lint_code() -> bool:
    """Lint code using ruff and mypy."""
    print_status("Linting code...")
    
    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")
    
    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False
    
    try:
        # Run ruff
        run_command(["ruff", "check", "."], cwd=backend_dir)
        
        # Run mypy
        run_command(["mypy", "app/"], cwd=backend_dir)
        
        print_success("Code linting completed")
        return True
    except subprocess.CalledProcessError:
        print_error("Code linting failed")
        return False


def run_tests() -> bool:
    """Run tests using pytest."""
    print_status("Running tests...")
    
    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")
    
    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False
    
    try:
        # Run pytest
        run_command([
            "pytest", "-v", 
            "--cov=app", 
            "--cov-report=html", 
            "--cov-report=term-missing"
        ], cwd=backend_dir)
        
        print_success("Tests completed")
        return True
    except subprocess.CalledProcessError:
        print_error("Tests failed")
        return False