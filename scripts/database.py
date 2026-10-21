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
    """Start database services (PostgreSQL and Redis) if Docker is available."""
    print_status("Starting database services...")

    if not check_docker():
        print_status("Docker daemon not running. SuperMon will use the built-in SQLite database engine.")
        return True

    # Start PostgreSQL
    try:
        result = run_command(["docker", "ps", "--filter", "name=supermon-postgres", "--format", "{{.Names}}"])
        if "supermon-postgres" in result.stdout:
            print_status("PostgreSQL already running")
        else:
            result = run_command(["docker", "ps", "-a", "--filter", "name=supermon-postgres", "--format", "{{.Names}}"])
            if "supermon-postgres" in result.stdout:
                run_command(["docker", "start", "supermon-postgres"])
            else:
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
        print_warning(f"Could not start PostgreSQL in Docker: {e}. Will fall back to SQLite.")

    # Start Redis
    try:
        result = run_command(["docker", "ps", "--filter", "name=supermon-redis", "--format", "{{.Names}}"])
        if "supermon-redis" in result.stdout:
            print_status("Redis already running")
        else:
            result = run_command(["docker", "ps", "-a", "--filter", "name=supermon-redis", "--format", "{{.Names}}"])
            if "supermon-redis" in result.stdout:
                run_command(["docker", "start", "supermon-redis"])
            else:
                run_command([
                    "docker", "run", "-d", "--name", "supermon-redis",
                    "-p", "6379:6379",
                    "redis:7-alpine"
                ])
            print_success("Redis started")
    except subprocess.CalledProcessError as e:
        print_warning(f"Could not start Redis in Docker: {e}")

    return True


def init_database() -> bool:
    """Initialize database schema."""
    print_status("Initializing database...")

    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")

    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False

    # Wait for PostgreSQL only if docker is actively running
    if check_docker():
        max_retries = 5
        retries = 0
        while retries < max_retries:
            try:
                run_command(["docker", "exec", "supermon-postgres", "pg_isready", "-U", "supermon"])
                break
            except subprocess.CalledProcessError:
                retries += 1
                time.sleep(1)

    # Run database initialization
    try:
        init_code = (
            "import sys; sys.path.insert(0, '.'); "
            "from app.core.database import init_db, SessionLocal; "
            "from app.core.seed import seed_initial_data; "
            "init_db(); "
            "db = SessionLocal(); "
            "seed_initial_data(db); "
            "db.close(); "
            "print('Database initialized and seeded successfully')"
        )
        run_command(["python", "-c", init_code], cwd=backend_dir, use_conda=True)
        print_success("Database initialized and ready")
        return True

    except (subprocess.CalledProcessError, IOError) as e:
        print_warning(f"Database init warning (non-fatal): {e}")
        return True


def stop_databases() -> bool:
    """Stop database services."""
    if not check_docker():
        return True

    print_status("Stopping database services...")
    try:
        run_command(["docker", "stop", "supermon-postgres", "supermon-redis"])
        print_success("Database containers stopped")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to stop database containers: {e}")
        return False