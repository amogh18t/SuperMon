#!/usr/bin/env python3
"""
SuperMon SDLC Automation Platform - Main Script

This script provides a command-line interface for managing the SuperMon platform.
It orchestrates the setup, starting, stopping, and monitoring of all components.
"""

import os
import sys
import time
import argparse
import signal
from typing import Dict, List, Optional

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from scripts.utils import (
    print_status, print_success, print_warning, print_error,
    get_project_root, COLORS
)
from scripts.environment import (
    setup_conda_env, setup_frontend_deps, check_env_file,
    run_code_quality_checks, format_code, lint_code, run_tests
)
from scripts.database import (
    start_databases, init_database, stop_databases
)
from scripts.services import (
    start_backend, start_frontend, start_mcp_servers,
    stop_backend, stop_frontend, stop_mcp_servers,
    stop_all_services, show_status
)


def handle_interrupt(signum, frame):
    """Handle interrupt signal (Ctrl+C)."""
    print("")
    print_warning("Received interrupt signal")
    stop_all_services()
    sys.exit(0)


def start_all():
    """Start all components of the SuperMon platform."""
    print_status("Starting SuperMon SDLC Automation Platform...")
    
    # Setup environment
    if not setup_conda_env():
        return False
    
    # Setup frontend dependencies
    if not setup_frontend_deps():
        return False
    
    # Check environment variables
    if not check_env_file():
        return False
    
    # Start databases
    if not start_databases():
        print_warning("Failed to start databases, continuing anyway...")
    
    # Initialize database
    if not init_database():
        print_warning("Failed to initialize database, continuing anyway...")
    
    # Start MCP servers
    if not start_mcp_servers():
        print_warning("Failed to start some MCP servers, continuing anyway...")
    
    # Start backend
    if not start_backend():
        print_error("Failed to start backend")
        return False
    
    # Start frontend
    if not start_frontend():
        print_error("Failed to start frontend")
        return False
    
    # Wait for services to start
    print_status("Waiting for services to start...")
    time.sleep(3)
    
    # Show status
    show_status()
    
    print_success("SuperMon platform started successfully!")
    print_warning("Don't forget to update your .env file with API keys!")
    
    return True


def setup_only():
    """Set up dependencies only without starting services."""
    print_status("Setting up SuperMon dependencies...")
    
    # Setup environment
    if not setup_conda_env():
        return False
    
    # Setup frontend dependencies
    if not setup_frontend_deps():
        return False
    
    # Check environment variables
    if not check_env_file():
        return False
    
    # Run code quality checks
    if not run_code_quality_checks():
        print_warning("Code quality checks failed, continuing anyway...")
    
    print_success("Setup completed!")
    return True


def quality_checks():
    """Run all code quality checks."""
    print_status("Running code quality checks...")
    
    # Format code
    if not format_code():
        print_warning("Code formatting failed")
    
    # Lint code
    if not lint_code():
        print_warning("Code linting failed")
    
    # Run tests
    if not run_tests():
        print_warning("Tests failed")
    
    print_success("Quality checks completed!")
    return True


def main():
    """Main function."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="SuperMon SDLC Automation Platform")
    parser.add_argument(
        "command",
        choices=[
            "start", "stop", "restart", "status",
            "setup", "test", "format", "lint", "quality"
        ],
        nargs="?",
        default="start",
        help="Command to execute"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "start":
        start_all()
    elif args.command == "stop":
        stop_all_services()
    elif args.command == "restart":
        stop_all_services()
        time.sleep(2)
        start_all()
    elif args.command == "status":
        show_status()
    elif args.command == "setup":
        setup_only()
    elif args.command == "test":
        run_tests()
    elif args.command == "format":
        format_code()
    elif args.command == "lint":
        lint_code()
    elif args.command == "quality":
        quality_checks()
    else:
        parser.print_help()


if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)
    
    # Print banner
    print(f"""
{COLORS['BLUE']}╔══════════════════════════════════════════════════════════╗{COLORS['NC']}
{COLORS['BLUE']}║                                                          ║{COLORS['NC']}
{COLORS['BLUE']}║  {COLORS['GREEN']}SuperMon SDLC Automation Platform{COLORS['BLUE']}                      ║{COLORS['NC']}
{COLORS['BLUE']}║  {COLORS['YELLOW']}Version 1.0.0{COLORS['BLUE']}                                        ║{COLORS['NC']}
{COLORS['BLUE']}║                                                          ║{COLORS['NC']}
{COLORS['BLUE']}╚══════════════════════════════════════════════════════════╝{COLORS['NC']}
    """)
    
    # Run main function
    main()