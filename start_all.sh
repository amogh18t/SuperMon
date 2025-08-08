#!/bin/bash

# SuperMon SDLC Automation Platform - Startup Script Wrapper
# This script is a wrapper around the Python-based supermon.py script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Export colors for the Python script
export RED="$RED"
export GREEN="$GREEN"
export YELLOW="$YELLOW"
export BLUE="$BLUE"
export NC="$NC"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Run the Python script
python3 "$(dirname "$0")/supermon.py" "$@"