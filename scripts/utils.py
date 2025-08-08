#!/usr/bin/env python3
"""
Utility functions for SuperMon scripts.
"""

import os
import sys
import subprocess
import time
import signal
from typing import List, Dict, Optional, Union, Any
import logging

# Try to import psutil, but provide fallback if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("supermon")

# ANSI Colors
COLORS = {
    "RED": "\033[0;31m",
    "GREEN": "\033[0;32m",
    "YELLOW": "\033[1;33m",
    "BLUE": "\033[0;34m",
    "MAGENTA": "\033[0;35m",
    "CYAN": "\033[0;36m",
    "NC": "\033[0m"  # No Color
}


def print_status(message: str) -> None:
    """Print status message."""
    logger.info(f"{COLORS['BLUE']}[INFO]{COLORS['NC']} {message}")


def print_success(message: str) -> None:
    """Print success message."""
    logger.info(f"{COLORS['GREEN']}[SUCCESS]{COLORS['NC']} {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    logger.warning(f"{COLORS['YELLOW']}[WARNING]{COLORS['NC']} {message}")


def print_error(message: str) -> None:
    """Print error message."""
    logger.error(f"{COLORS['RED']}[ERROR]{COLORS['NC']} {message}")


def run_command(cmd: List[str], cwd: Optional[str] = None, use_conda: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    if use_conda:
        cmd = ["conda", "run", "-n", "supermon"] + cmd
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)}")
        print_error(f"Error: {e.stderr}")
        raise


def run_background_process(cmd: List[str], cwd: Optional[str] = None, pid_file: Optional[str] = None, use_conda: bool = False) -> int:
    """Run a command in the background and optionally save its PID to a file."""
    if use_conda:
        cmd = ["conda", "run", "-n", "supermon"] + cmd
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )

    # Save PID to file if requested
    if pid_file:
        try:
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
                f.flush()
                os.fsync(f.fileno())  # Ensure it's written to disk

            # Verify the PID was written correctly
            with open(pid_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    print_error(f"Failed to write PID to file: {pid_file}")
        except Exception as e:
            print_error(f"Error writing PID file: {e}")

    return process.pid


def check_process_running(pid_file: str) -> bool:
    """Check if a process is running based on its PID file."""
    if not os.path.exists(pid_file):
        return False

    try:
        with open(pid_file, 'r') as f:
            content = f.read().strip()
            if not content:
                print_warning(f"PID file exists but is empty: {pid_file}")
                return False
            pid = int(content)

        # Check if process is running
        is_running = False
        if HAS_PSUTIL:
            is_running = psutil.pid_exists(pid)
        else:
            # Fallback implementation using os.kill with signal 0
            # This just tests if the process exists, doesn't actually send a signal
            try:
                os.kill(pid, 0)
                is_running = True
            except OSError:
                is_running = False

        if not is_running:
            print_warning(f"Process with PID {pid} from {pid_file} is not running")

        return is_running
    except (ValueError, IOError) as e:
        print_warning(f"Error checking PID file {pid_file}: {e}")
        return False


def stop_process(pid_file: str) -> bool:
    """Stop a process based on its PID file."""
    if not os.path.exists(pid_file):
        return True

    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        # Try to terminate the process group
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            # Give it a moment to terminate gracefully
            time.sleep(2)

            # If still running, force kill
            is_running = False
            if HAS_PSUTIL:
                is_running = psutil.pid_exists(pid)
            else:
                try:
                    os.kill(pid, 0)
                    is_running = True
                except OSError:
                    is_running = False

            if is_running:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        except ProcessLookupError:
            # Process already gone
            pass

        # Remove PID file
        os.remove(pid_file)
        return True
    except (ValueError, IOError) as e:
        print_error(f"Error stopping process: {e}")
        return False


def check_conda() -> bool:
    """Check if conda is available."""
    try:
        run_command(["conda", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_docker() -> bool:
    """Check if docker is available."""
    try:
        run_command(["docker", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_project_root() -> str:
    """Get the project root directory."""
    # Assuming this script is in the scripts directory
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env_file(env_file: str) -> Dict[str, str]:
    """Load environment variables from a .env file."""
    env_vars = {}

    if not os.path.exists(env_file):
        return env_vars

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()

    return env_vars