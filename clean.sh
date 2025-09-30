#!/bin/bash
# Unified Security Tools Suite - Cleanup Script
# Author: OK2HSS
# Version: 1.0.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Unified Security Tools Suite - Cleanup${NC}"
echo -e "${BLUE}   Author: OK2HSS | Version: 1.0.0${NC}"
echo ""

# Function to clean Python cache
clean_python_cache() {
    echo -e "${YELLOW}🗑️  Cleaning Python cache files...${NC}"
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .pyc and .pyo files
    find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Python cache cleaned${NC}"
}

# Function to clean virtual environment
clean_venv() {
    echo -e "${YELLOW}🗑️  Removing virtual environment...${NC}"
    
    if [ -d "venv" ]; then
        rm -rf venv
        echo -e "${GREEN}✅ Virtual environment removed${NC}"
    else
        echo -e "${BLUE}ℹ️  No virtual environment found${NC}"
    fi
}

# Function to clean logs
clean_logs() {
    echo -e "${YELLOW}🗑️  Cleaning log files...${NC}"
    
    if [ -d "wifi_logs" ]; then
        rm -f wifi_logs/*.log wifi_logs/*.json 2>/dev/null || true
        echo -e "${GREEN}✅ Log files cleaned${NC}"
    else
        echo -e "${BLUE}ℹ️  No log directory found${NC}"
    fi
}

# Function to clean temporary files
clean_temp() {
    echo -e "${YELLOW}🗑️  Cleaning temporary files...${NC}"
    
    find . -type f \( -name "*.tmp" -o -name "*.bak" -o -name "*~" \) -delete 2>/dev/null || true
    find . -type f -name ".DS_Store" -delete 2>/dev/null || true
    
    echo -e "${GREEN}✅ Temporary files cleaned${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  ./clean.sh [options]"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  --all        Clean everything (cache, venv, logs, temp)"
    echo "  --cache      Clean only Python cache files"
    echo "  --venv       Remove virtual environment"
    echo "  --logs       Clean log files"
    echo "  --temp       Clean temporary files"
    echo "  --help       Show this help message"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  ./clean.sh --all      # Full cleanup"
    echo "  ./clean.sh --cache    # Clean only cache"
    echo "  ./clean.sh            # Interactive mode"
}

# Main execution
main() {
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --all)
            echo -e "${YELLOW}🧹 Performing full cleanup...${NC}"
            echo ""
            clean_python_cache
            clean_venv
            clean_logs
            clean_temp
            echo ""
            echo -e "${GREEN}✅ Full cleanup complete!${NC}"
            exit 0
            ;;
        --cache)
            clean_python_cache
            exit 0
            ;;
        --venv)
            clean_venv
            exit 0
            ;;
        --logs)
            clean_logs
            exit 0
            ;;
        --temp)
            clean_temp
            exit 0
            ;;
        "")
            # Interactive mode
            echo -e "${YELLOW}Select cleanup options:${NC}"
            echo "  1. Clean Python cache"
            echo "  2. Remove virtual environment"
            echo "  3. Clean log files"
            echo "  4. Clean temporary files"
            echo "  5. Clean everything"
            echo "  q. Cancel"
            echo ""
            read -p "Select option (1-5, q): " choice
            
            case "$choice" in
                1)
                    clean_python_cache
                    ;;
                2)
                    clean_venv
                    ;;
                3)
                    clean_logs
                    ;;
                4)
                    clean_temp
                    ;;
                5)
                    echo ""
                    clean_python_cache
                    clean_venv
                    clean_logs
                    clean_temp
                    echo ""
                    echo -e "${GREEN}✅ Full cleanup complete!${NC}"
                    ;;
                q|Q)
                    echo -e "${BLUE}Cleanup cancelled${NC}"
                    exit 0
                    ;;
                *)
                    echo -e "${RED}❌ Invalid option${NC}"
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

