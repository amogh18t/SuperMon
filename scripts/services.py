#!/usr/bin/env python3
"""
Service management for SuperMon (backend, frontend, and MCP servers).
"""

import os
import sys
import subprocess
import time
from typing import Dict, List, Optional, Tuple

from scripts.utils import (
    print_status, print_success, print_warning, print_error,
    run_command, run_background_process, check_process_running,
    stop_process, get_project_root, check_docker
)


def start_backend() -> bool:
    """Start the backend server."""
    print_status("Starting backend server...")

    project_root = get_project_root()
    backend_dir = os.path.join(project_root, "backend")
    pid_file = os.path.join(project_root, "backend.pid")

    if not os.path.exists(backend_dir):
        print_error(f"Backend directory not found: {backend_dir}")
        return False

    # Check if backend is already running
    if check_process_running(pid_file):
        print_status("Backend server is already running")
        return True

    try:
        # Start FastAPI server
        cmd = ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        run_background_process(cmd, cwd=backend_dir, pid_file=pid_file, use_conda=True)

        print_success("Backend server started on http://localhost:8000")
        return True
    except Exception as e:
        print_error(f"Failed to start backend server: {e}")
        return False


def start_frontend() -> bool:
    """Start the frontend server."""
    print_status("Starting frontend server...")

    project_root = get_project_root()
    frontend_dir = os.path.join(project_root, "frontend")
    pid_file = os.path.join(project_root, "frontend.pid")

    if not os.path.exists(frontend_dir):
        print_error(f"Frontend directory not found: {frontend_dir}")
        return False

    # Check if frontend is already running
    if check_process_running(pid_file):
        print_status("Frontend server is already running")
        return True

    try:
        # Start Next.js development server
        cmd = ["npm", "run", "dev"]
        run_background_process(cmd, cwd=frontend_dir, pid_file=pid_file)

        print_success("Frontend server started on http://localhost:3000")
        return True
    except Exception as e:
        print_error(f"Failed to start frontend server: {e}")
        return False


def start_mcp_servers() -> bool:
    """Start all MCP servers."""
    print_status("Starting MCP servers...")

    project_root = get_project_root()
    mcp_dir = os.path.join(project_root, "mcp_servers")

    if not os.path.exists(mcp_dir):
        print_error(f"MCP servers directory not found: {mcp_dir}")
        return False

    # List of MCP servers to start
    mcp_servers = [
        ("slack_mcp", "slack_mcp.py"),
        ("whatsapp_mcp", "whatsapp_mcp.py"),
        ("notion_mcp", "notion_mcp.py"),
        ("github_mcp", "github_mcp.py")
    ]

    success = True
    for mcp_name, mcp_script in mcp_servers:
        mcp_path = os.path.join(mcp_dir, mcp_name, mcp_script)
        pid_file = os.path.join(project_root, f"{mcp_name}.pid")

        # Check if MCP server exists
        if not os.path.exists(mcp_path):
            print_warning(f"{mcp_name} script not found, skipping")
            continue

        # Check if MCP server is already running
        if check_process_running(pid_file):
            print_status(f"{mcp_name} is already running")
            continue

        try:
            # Start MCP server
            mcp_server_dir = os.path.dirname(mcp_path)
            cmd = ["python", os.path.basename(mcp_path)]
            run_background_process(cmd, cwd=mcp_server_dir, pid_file=pid_file, use_conda=True)

            print_success(f"{mcp_name} started")
        except Exception as e:
            print_error(f"Failed to start {mcp_name}: {e}")
            success = False

    return success


def stop_backend() -> bool:
    """Stop the backend server."""
    print_status("Stopping backend server...")

    project_root = get_project_root()
    pid_file = os.path.join(project_root, "backend.pid")

    if stop_process(pid_file):
        print_success("Backend server stopped")
        return True
    else:
        print_error("Failed to stop backend server")
        return False


def stop_frontend() -> bool:
    """Stop the frontend server."""
    print_status("Stopping frontend server...")

    project_root = get_project_root()
    pid_file = os.path.join(project_root, "frontend.pid")

    if stop_process(pid_file):
        print_success("Frontend server stopped")
        return True
    else:
        print_error("Failed to stop frontend server")
        return False


def stop_mcp_servers() -> bool:
    """Stop all MCP servers."""
    print_status("Stopping MCP servers...")

    project_root = get_project_root()
    mcp_servers = ["slack_mcp", "whatsapp_mcp", "notion_mcp", "github_mcp"]

    success = True
    for mcp_name in mcp_servers:
        pid_file = os.path.join(project_root, f"{mcp_name}.pid")

        if stop_process(pid_file):
            print_success(f"{mcp_name} stopped")
        else:
            print_warning(f"Failed to stop {mcp_name} or not running")
            success = False

    return success


def stop_all_services() -> bool:
    """Stop all services (backend, frontend, and MCP servers)."""
    print_status("Stopping all services...")

    backend_stopped = stop_backend()
    frontend_stopped = stop_frontend()
    mcp_stopped = stop_mcp_servers()

    return backend_stopped and frontend_stopped and mcp_stopped


def show_status() -> None:
    """Show the status of all services."""
    print_status("Checking service status...")

    project_root = get_project_root()

    print("")
    print("📊 Service Status:")
    print("==================")

    # Backend
    backend_pid_file = os.path.join(project_root, "backend.pid")
    if check_process_running(backend_pid_file):
        print(f"{os.environ.get('GREEN', '')}✓{os.environ.get('NC', '')} Backend (http://localhost:8000)")
    else:
        print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} Backend")

    # Frontend
    frontend_pid_file = os.path.join(project_root, "frontend.pid")
    if check_process_running(frontend_pid_file):
        print(f"{os.environ.get('GREEN', '')}✓{os.environ.get('NC', '')} Frontend (http://localhost:3000)")
    else:
        print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} Frontend")

    # MCP Servers
    mcp_servers = [
        ("slack_mcp", "Slack MCP"),
        ("whatsapp_mcp", "WhatsApp MCP"),
        ("notion_mcp", "Notion MCP"),
        ("github_mcp", "GitHub MCP")
    ]

    for mcp_file, mcp_display in mcp_servers:
        pid_file = os.path.join(project_root, f"{mcp_file}.pid")
        if check_process_running(pid_file):
            print(f"{os.environ.get('GREEN', '')}✓{os.environ.get('NC', '')} {mcp_display}")
        else:
            print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} {mcp_display}")

    # Databases
    if check_docker():
        try:
            result = run_command(["docker", "ps", "--filter", "name=supermon-postgres", "--format", "{{.Names}}"])
            if "supermon-postgres" in result.stdout:
                print(f"{os.environ.get('GREEN', '')}✓{os.environ.get('NC', '')} PostgreSQL")
            else:
                print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} PostgreSQL")

            result = run_command(["docker", "ps", "--filter", "name=supermon-redis", "--format", "{{.Names}}"])
            if "supermon-redis" in result.stdout:
                print(f"{os.environ.get('GREEN', '')}✓{os.environ.get('NC', '')} Redis")
            else:
                print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} Redis")
        except subprocess.CalledProcessError:
            print(f"{os.environ.get('RED', '')}✗{os.environ.get('NC', '')} Database status check failed")

    print("")
    print("🌐 Access Points:")
    print("==================")
    print("Frontend Dashboard: http://localhost:3000")
    print("API Documentation:  http://localhost:8000/docs")
    print("Health Check:       http://localhost:8000/health")
    print("")