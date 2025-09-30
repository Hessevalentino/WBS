#!/bin/bash
# Unified Security Tools Suite - Launcher Script
# Author: OK2HSS
# Version: 1.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🛡️  Unified Security Tools Suite${NC}"
echo -e "${BLUE}   Author: OK2HSS | Version: 1.0.0${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
        return 0
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
}

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${YELLOW}📦 Installing/updating dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    echo -e "${GREEN}✅ Virtual environment ready${NC}"
}

# Function to check system dependencies
check_system_deps() {
    echo -e "${YELLOW}🔍 Checking system dependencies...${NC}"
    
    local missing_deps=()
    
    # Check for Bluetooth
    if ! command_exists bluetoothctl; then
        missing_deps+=("bluetooth/bluez")
    fi
    
    # Check for NetworkManager
    if ! command_exists nmcli; then
        missing_deps+=("network-manager")
    fi
    
    # Check for wireless tools
    if ! command_exists iwconfig; then
        missing_deps+=("wireless-tools")
    fi
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All system dependencies found${NC}"
    else
        echo -e "${YELLOW}⚠️  Missing system dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}💡 Install with:${NC}"
        echo -e "${YELLOW}   Ubuntu/Debian: sudo apt install bluetooth bluez network-manager wireless-tools${NC}"
        echo -e "${YELLOW}   Fedora/RHEL:   sudo dnf install bluez NetworkManager wireless-tools${NC}"
        echo ""
    fi
}

# Function to check permissions
check_permissions() {
    if [ "$EUID" -eq 0 ]; then
        echo -e "${GREEN}✅ Running as root - full functionality available${NC}"
    else
        echo -e "${YELLOW}⚠️  Running as regular user${NC}"
        echo -e "${YELLOW}💡 For full functionality, consider:${NC}"
        echo -e "${YELLOW}   sudo ./run.sh${NC}"
        echo -e "${YELLOW}   or${NC}"
        echo -e "${YELLOW}   sudo setcap 'cap_net_raw,cap_net_admin+eip' \$(which python3)${NC}"
    fi
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  ./run.sh [options]"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  --setup          Setup virtual environment and dependencies"
    echo "  --pytag          Run PyTAG directly (Rich UI)"
    echo "  --pytag-simple   Run PyTAG in simple mode"
    echo "  --wss            Run WSS continuous scan"
    echo "  --check          Check system dependencies and permissions"
    echo "  --help           Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  ./run.sh                # Interactive menu"
    echo "  ./run.sh --setup        # Setup environment"
    echo "  ./run.sh --pytag        # Run PyTAG"
    echo "  ./run.sh --wss          # Run WSS"
    echo "  sudo ./run.sh           # Run with root privileges"
}

# Main execution
main() {
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --setup)
            echo -e "${BLUE}🔧 Setting up Unified Security Tools Suite...${NC}"
            check_python || exit 1
            setup_venv
            check_system_deps
            check_permissions
            echo -e "${GREEN}✅ Setup complete! Run './run.sh' to start the application.${NC}"
            exit 0
            ;;
        --check)
            check_python || exit 1
            check_system_deps
            check_permissions
            exit 0
            ;;
        --pytag)
            if [ ! -d "venv" ]; then
                echo -e "${YELLOW}📦 Virtual environment not found. Setting up...${NC}"
                setup_venv
            fi
            source venv/bin/activate
            python3 wbs.py --pytag
            exit 0
            ;;
        --pytag-simple)
            if [ ! -d "venv" ]; then
                echo -e "${YELLOW}📦 Virtual environment not found. Setting up...${NC}"
                setup_venv
            fi
            source venv/bin/activate
            python3 wbs.py --pytag --simple
            exit 0
            ;;
        --wss)
            if [ ! -d "venv" ]; then
                echo -e "${YELLOW}📦 Virtual environment not found. Setting up...${NC}"
                setup_venv
            fi
            source venv/bin/activate
            python3 wbs.py --wss
            exit 0
            ;;
        "")
            # Default: run interactive menu
            if [ ! -d "venv" ]; then
                echo -e "${YELLOW}📦 Virtual environment not found. Setting up...${NC}"
                setup_venv
            fi
            source venv/bin/activate
            python3 wbs.py
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Check if Python is available
if ! check_python; then
    echo -e "${RED}❌ Python 3 is required but not found${NC}"
    echo -e "${YELLOW}💡 Install Python 3:${NC}"
    echo -e "${YELLOW}   Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip${NC}"
    echo -e "${YELLOW}   Fedora/RHEL:   sudo dnf install python3 python3-pip${NC}"
    exit 1
fi

# Run main function
main "$@"
