#!/bin/bash
# Unified Security Tools Suite - Installation Script
# Author: OK2HSS
# Version: 1.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                              ║${NC}"
echo -e "${CYAN}║                    🛡️  Unified Security Tools Suite                         ║${NC}"
echo -e "${CYAN}║                           Installation Script                               ║${NC}"
echo -e "${CYAN}║                                                                              ║${NC}"
echo -e "${CYAN}║                         Author: OK2HSS | Version: 1.0.0                    ║${NC}"
echo -e "${CYAN}║                                                                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/redhat-release ]; then
        OS="Red Hat Enterprise Linux"
        VER=$(cat /etc/redhat-release | sed 's/.*release //' | sed 's/ .*//')
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    echo -e "${BLUE}🖥️  Detected OS: ${OS} ${VER}${NC}"
}

# Function to install system dependencies
install_system_deps() {
    echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
    
    if command -v apt-get >/dev/null 2>&1; then
        # Debian/Ubuntu
        echo -e "${BLUE}Using apt package manager...${NC}"
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv python3-pip bluetooth bluez network-manager wireless-tools
        
        # Optional tools
        echo -e "${YELLOW}Installing optional tools...${NC}"
        sudo apt-get install -y arp-scan nmap || echo -e "${YELLOW}⚠️  Optional tools not installed${NC}"
        
    elif command -v dnf >/dev/null 2>&1; then
        # Fedora/RHEL 8+
        echo -e "${BLUE}Using dnf package manager...${NC}"
        sudo dnf install -y python3 python3-pip bluez NetworkManager wireless-tools
        
        # Optional tools
        echo -e "${YELLOW}Installing optional tools...${NC}"
        sudo dnf install -y arp-scan nmap || echo -e "${YELLOW}⚠️  Optional tools not installed${NC}"
        
    elif command -v yum >/dev/null 2>&1; then
        # RHEL/CentOS 7
        echo -e "${BLUE}Using yum package manager...${NC}"
        sudo yum install -y python3 python3-pip bluez NetworkManager wireless-tools
        
        # Optional tools
        echo -e "${YELLOW}Installing optional tools...${NC}"
        sudo yum install -y nmap || echo -e "${YELLOW}⚠️  Optional tools not installed${NC}"
        
    elif command -v pacman >/dev/null 2>&1; then
        # Arch Linux
        echo -e "${BLUE}Using pacman package manager...${NC}"
        sudo pacman -S --noconfirm python python-pip bluez networkmanager wireless_tools
        
        # Optional tools
        echo -e "${YELLOW}Installing optional tools...${NC}"
        sudo pacman -S --noconfirm arp-scan nmap || echo -e "${YELLOW}⚠️  Optional tools not installed${NC}"
        
    else
        echo -e "${RED}❌ Unsupported package manager${NC}"
        echo -e "${YELLOW}💡 Please install manually:${NC}"
        echo -e "${YELLOW}   - Python 3.8+${NC}"
        echo -e "${YELLOW}   - Bluetooth/BlueZ${NC}"
        echo -e "${YELLOW}   - NetworkManager${NC}"
        echo -e "${YELLOW}   - Wireless tools${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Function to setup Python environment
setup_python_env() {
    echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
    else
        echo -e "${RED}❌ Python 3 not found${NC}"
        return 1
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate and install dependencies
    echo -e "${YELLOW}🔄 Installing Python dependencies...${NC}"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Python environment ready${NC}"
}

# Function to setup services
setup_services() {
    echo -e "${YELLOW}🔧 Setting up system services...${NC}"
    
    # Enable Bluetooth
    if systemctl is-enabled bluetooth >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Bluetooth service already enabled${NC}"
    else
        echo -e "${YELLOW}🔄 Enabling Bluetooth service...${NC}"
        sudo systemctl enable bluetooth
        sudo systemctl start bluetooth
    fi
    
    # Enable NetworkManager
    if systemctl is-enabled NetworkManager >/dev/null 2>&1; then
        echo -e "${GREEN}✅ NetworkManager already enabled${NC}"
    else
        echo -e "${YELLOW}🔄 Enabling NetworkManager...${NC}"
        sudo systemctl enable NetworkManager
        sudo systemctl start NetworkManager
    fi
    
    echo -e "${GREEN}✅ Services configured${NC}"
}

# Function to set permissions
setup_permissions() {
    echo -e "${YELLOW}🔐 Setting up permissions...${NC}"
    
    # Add user to bluetooth group
    if groups $USER | grep -q bluetooth; then
        echo -e "${GREEN}✅ User already in bluetooth group${NC}"
    else
        echo -e "${YELLOW}🔄 Adding user to bluetooth group...${NC}"
        sudo usermod -a -G bluetooth $USER
        echo -e "${YELLOW}⚠️  You need to logout and login again for group changes to take effect${NC}"
    fi
    
    # Set capabilities for Python (optional)
    echo -e "${YELLOW}💡 Setting Python capabilities for BLE access...${NC}"
    sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3) || echo -e "${YELLOW}⚠️  Could not set capabilities${NC}"
    
    echo -e "${GREEN}✅ Permissions configured${NC}"
}

# Function to create desktop entry
create_desktop_entry() {
    echo -e "${YELLOW}🖥️  Creating desktop entry...${NC}"
    
    DESKTOP_FILE="$HOME/.local/share/applications/unified-security-tools.desktop"
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Unified Security Tools Suite
Comment=PyTAG AirTag Detector and WiFi Scanner Suite
Exec=$SCRIPT_DIR/run.sh
Icon=security-high
Terminal=true
Type=Application
Categories=Network;Security;
Keywords=security;bluetooth;wifi;airtag;scanner;
EOF
    
    chmod +x "$DESKTOP_FILE"
    echo -e "${GREEN}✅ Desktop entry created${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}🧪 Running basic tests...${NC}"
    
    # Test Python imports
    source venv/bin/activate
    python3 -c "import sys; print(f'Python {sys.version}')"
    python3 -c "import bleak; print('✅ bleak imported successfully')"
    python3 -c "import rich; print('✅ rich imported successfully')"
    
    # Test application help
    python3 wbs.py --help >/dev/null && echo -e "${GREEN}✅ Application help works${NC}"
    
    # Test modules
    python3 -c "from modules import pytag_module, wss_module; print('✅ Modules imported successfully')"
    
    echo -e "${GREEN}✅ Basic tests passed${NC}"
}

# Main installation function
main() {
    echo -e "${BLUE}🚀 Starting installation...${NC}"
    echo ""
    
    # Detect OS
    detect_os
    echo ""
    
    # Check if running as root for system packages
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}⚠️  This script will use sudo for system package installation${NC}"
        echo -e "${YELLOW}💡 You may be prompted for your password${NC}"
        echo ""
    fi
    
    # Install system dependencies
    install_system_deps
    echo ""
    
    # Setup Python environment
    setup_python_env
    echo ""
    
    # Setup services
    setup_services
    echo ""
    
    # Setup permissions
    setup_permissions
    echo ""
    
    # Create desktop entry
    create_desktop_entry
    echo ""
    
    # Run tests
    run_tests
    echo ""
    
    # Final message
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║                    🎉 Installation Complete! 🎉                             ║${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║  Unified Security Tools Suite is now ready to use!                          ║${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║  Usage:                                                                      ║${NC}"
    echo -e "${GREEN}║    ./run.sh                    # Interactive menu                            ║${NC}"
    echo -e "${GREEN}║    ./run.sh --pytag            # Run PyTAG                                   ║${NC}"
    echo -e "${GREEN}║    ./run.sh --wss              # Run WSS                                     ║${NC}"
    echo -e "${GREEN}║    sudo ./run.sh               # Run with full privileges                    ║${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}║  For best results, logout and login again to apply group changes.          ║${NC}"
    echo -e "${GREEN}║                                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo -e "${BLUE}Unified Security Tools Suite - Installation Script${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  ./install.sh        # Full installation"
    echo "  ./install.sh --help # Show this help"
    echo ""
    echo -e "${BLUE}This script will:${NC}"
    echo "  • Install system dependencies (Bluetooth, NetworkManager, etc.)"
    echo "  • Setup Python virtual environment"
    echo "  • Install Python dependencies"
    echo "  • Configure system services"
    echo "  • Set up permissions"
    echo "  • Create desktop entry"
    echo "  • Run basic tests"
    echo ""
    exit 0
fi

# Run main installation
main
