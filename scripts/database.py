#!/usr/bin/env python3
"""
Database management for SuperMon.
"""

import os
import sys
import subprocess
import time
from typing import Dict, List, Optional

from scripts.utils import (
    print_status, print_success, print_warning, print_error,
    run_command, check_docker, get_project_root
)


def start_databases() -> bool:
    """Start database services (PostgreSQL and Redis)."""
    print_status("Starting database services...")
    
    if not check_docker():
        print_warning("Docker not available. Please start PostgreSQL and Redis manually.")
        return False
    
    # Start PostgreSQL
    try:
        # Check if PostgreSQL container is already running
        result = run_command(["docker", "ps", "--filter", "name=supermon-postgres", "--format", "{{.Names}}"])
        if "supermon-postgres" in result.stdout:
            print_status("PostgreSQL already running")
        else:
            # Check if container exists but is stopped
            result = run_command(["docker", "ps", "-a", "--filter", "name=supermon-postgres", "--format", "{{.Names}}"])
            if "supermon-postgres" in result.stdout:
                run_command(["docker", "start", "supermon-postgres"])
            else:
                # Create and start container
                run_command([
                    "docker", "run", "-d", "--name", "supermon-postgres",
                    "-e", "POSTGRES_DB=supermon",
                    "-e", "POSTGRES_USER=supermon",
                    "-e", "POSTGRES_PASSWORD=supermon123",
                    "-p", "5432:5432",
                    "postgres:15"
                ])
            print_success("PostgreSQL started")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start PostgreSQL: {e}")
        return False
    
    # Start Redis
    try:
        # Check if Redis container is already running
        result = run_command(["docker", "ps", "--filter", "name=supermon-redis", "--format", "{{.Names}}"])
        if "supermon-redis" in result.stdout:
            print_status("Redis already running")
        else:
            # Check if container exists but is stopped
            result = run_command(["docker", "ps", "-a", "--filter", "name=supermon-redis", "--format", "{{.Names}}"])
            if "supermon-redis" in result.stdout:
                run_command(["docker", "start", "supermon-redis"])
            else:
                # Create and start container
                run_command([
                    "docker", "run", "-d", "--name", "supermon-redis",
                    "-p", "6379:6379",
                    "redis:7-alpine"
                ])
            print_success("Redis started")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start Redis: {e}")
        return False
    
    return True


def init_database() -> bool:
    """Initialize database schema."""
    print_status("Initializing database...")
    
    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")
    
    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False
    
    # Wait for PostgreSQL to be ready
    if check_docker():
        print_status("Waiting for PostgreSQL to be ready...")
        max_retries = 30
        retries = 0
        while retries < max_retries:
            try:
                run_command(["docker", "exec", "supermon-postgres", "pg_isready", "-U", "supermon"])
                break
            except subprocess.CalledProcessError:
                retries += 1
                time.sleep(1)
                if retries >= max_retries:
                    print_error("PostgreSQL did not become ready in time")
                    return False
    
    # Run database initialization
    try:
        # Create a Python script to initialize the database
        init_script = """
from app.core.database import init_db
init_db()
print('Database initialized successfully')
        """
        
        # Write the script to a temporary file
        temp_script = os.path.join(backend_dir, "init_db_temp.py")
        with open(temp_script, 'w') as f:
            f.write(init_script)
        
        # Run the script
        run_command(["python", "init_db_temp.py"], cwd=backend_dir)
        
        # Clean up
        os.remove(temp_script)
        
        print_success("Database initialized")
        return True
    except (subprocess.CalledProcessError, IOError) as e:
        print_error(f"Failed to initialize database: {e}")
        return False


def stop_databases() -> bool:
    """Stop database services."""
    print_status("Stopping database services...")
    
    if not check_docker():
        print_warning("Docker not available. Please stop PostgreSQL and Redis manually.")
        return False
    
    try:
        # Stop PostgreSQL and Redis containers
        run_command(["docker", "stop", "supermon-postgres", "supermon-redis"])
        print_success("Database containers stopped")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to stop database containers: {e}")
        return False