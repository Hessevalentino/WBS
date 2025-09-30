#!/usr/bin/env python3
"""
WBS - WiFi Bluetooth Suite
Unified Security Tools Suite
Author: OK2HSS
Version: 1.0.0

Unified application combining:
- PyTAG: Apple AirTag detector using BLE scanning
- WSS: WiFi Scanner Suite for network analysis

Professional security toolkit with intuitive interface.
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  For better appearance install rich: pip install rich")

# Import our modules
try:
    from modules.pytag_module import run_pytag, check_bluetooth_permissions
    from modules.wss_module import run_wss_continuous, run_wss_autoconnect, run_wss_statistics
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    MODULES_AVAILABLE = False


def show_main_banner():
    """Display main application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ██╗    ██╗██████╗ ███████╗                                                 ║
║  ██║    ██║██╔══██╗██╔════╝                                                 ║
║  ██║ █╗ ██║██████╔╝███████╗                                                 ║
║  ██║███╗██║██╔══██╗╚════██║                                                 ║
║  ╚███╔███╔╝██████╔╝███████║                                                 ║
║   ╚══╝╚══╝ ╚═════╝ ╚══════╝                                                 ║
║                                                                              ║
║              ╦ ╦┬┌─┐┬  ┬  ┌┐ ┬  ┬ ┬┌─┐┌┬┐┌─┐┌─┐┌┬┐┬ ┬  ╔═╗┬ ┬┬┌┬┐┌─┐       ║
║              ║║║│├┤ │  │  ├┴┐│  │ │├┤  │ │ ││ │ │ ├─┤  ╚═╗│ ││ │ ├┤        ║
║              ╚╩╝┴└  ┴  ┴  └─┘┴─┘└─┘└─┘ ┴ └─┘└─┘ ┴ ┴ ┴  ╚═╝└─┘┴ ┴ └─┘       ║
║                                                                              ║
║                           Author: OK2HSS | Version: 1.0.0                   ║
║                                                                              ║
║                    🏷️  PyTAG - Apple AirTag Detector                        ║
║                    📡 WSS - WiFi Scanner Suite                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    return banner


def show_simple_banner():
    """Display simple banner for terminals without rich"""
    banner = """
================================================================================

  ██╗    ██╗██████╗ ███████╗
  ██║    ██║██╔══██╗██╔════╝
  ██║ █╗ ██║██████╔╝███████╗
  ██║███╗██║██╔══██╗╚════██║
  ╚███╔███╔╝██████╔╝███████║
   ╚══╝╚══╝ ╚═════╝ ╚══════╝

                WiFi Bluetooth Suite
                Security Tools Suite
                Author: OK2HSS | Version: 1.0.0

                🏷️  PyTAG - Apple AirTag Detector
                📡 WSS - WiFi Scanner Suite

================================================================================
    """
    return banner


class UnifiedSecurityApp:
    """Main unified security application"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.running = True
        
    def show_banner(self):
        """Display application banner"""
        if RICH_AVAILABLE:
            banner = show_main_banner()
            self.console.print(f"[bold green]{banner}[/bold green]")
        else:
            banner = show_simple_banner()
            print(banner)
        
        # Add a small pause for dramatic effect
        time.sleep(1)
    
    def show_main_menu(self):
        """Display main menu"""
        if RICH_AVAILABLE:
            menu_text = """
[bold cyan]PyTAG - AirTag Detector:[/bold cyan]
  [bold yellow]1.[/bold yellow] 🏷️  Run PyTAG (Rich UI)
  [bold yellow]2.[/bold yellow] 🏷️  Run PyTAG (Simple mode)

[bold cyan]WSS - WiFi Scanner Suite:[/bold cyan]
  [bold yellow]3.[/bold yellow] 📡 Continuous WiFi scanning
  [bold yellow]4.[/bold yellow] 🔄 Auto-connect to open networks
  [bold yellow]5.[/bold yellow] 📊 Show WiFi statistics

[bold cyan]System:[/bold cyan]
  [bold yellow]6.[/bold yellow] ℹ️  Show system information
  [bold yellow]7.[/bold yellow] ⚙️  Check dependencies
  [bold yellow]q.[/bold yellow] ❌ Exit application
"""
            panel = Panel(
                menu_text,
                title="🛡️  WBS - WiFi Bluetooth Suite",
                border_style="blue",
                box=box.ROUNDED
            )
            self.console.print(panel)
        else:
            print("\n" + "="*80)
            print("🛡️  WBS - WiFi Bluetooth Suite")
            print("="*80)
            print("\nPyTAG - AirTag Detector:")
            print("  1. 🏷️  Run PyTAG (Rich UI)")
            print("  2. 🏷️  Run PyTAG (Simple mode)")
            print("\nWSS - WiFi Scanner Suite:")
            print("  3. 📡 Continuous WiFi scanning")
            print("  4. 🔄 Auto-connect to open networks")
            print("  5. 📊 Show WiFi statistics")
            print("\nSystem:")
            print("  6. ℹ️  Show system information")
            print("  7. ⚙️  Check dependencies")
            print("  q. ❌ Exit application")
    
    def show_system_info(self):
        """Show system information"""
        if RICH_AVAILABLE:
            table = Table(title="🖥️  System Information")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details", style="yellow")
            
            # Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            table.add_row("Python", "✅ Available", python_version)
            
            # Rich library
            if RICH_AVAILABLE:
                table.add_row("Rich UI", "✅ Available", "Enhanced interface enabled")
            else:
                table.add_row("Rich UI", "❌ Missing", "pip install rich")
            
            # Modules
            if MODULES_AVAILABLE:
                table.add_row("Security Modules", "✅ Available", "PyTAG + WSS loaded")
            else:
                table.add_row("Security Modules", "❌ Error", "Module import failed")
            
            # Operating System
            import platform
            table.add_row("Operating System", "ℹ️  Info", platform.system())
            table.add_row("Architecture", "ℹ️  Info", platform.machine())
            
            self.console.print(table)
        else:
            print("\n🖥️  System Information:")
            print("="*50)
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            print(f"Python: ✅ {python_version}")
            print(f"Rich UI: {'✅ Available' if RICH_AVAILABLE else '❌ Missing (pip install rich)'}")
            print(f"Modules: {'✅ Available' if MODULES_AVAILABLE else '❌ Error'}")
            
            import platform
            print(f"OS: {platform.system()} {platform.machine()}")
    
    def check_dependencies(self):
        """Check system dependencies"""
        print("\n🔍 Checking system dependencies...")
        print("="*50)
        
        # Python dependencies
        deps = {
            "rich": RICH_AVAILABLE,
            "modules": MODULES_AVAILABLE
        }
        
        for dep, available in deps.items():
            status = "✅ OK" if available else "❌ Missing"
            print(f"{dep:20} {status}")
        
        # System commands for WSS
        system_deps = ['nmcli', 'ping', 'iwconfig', 'bluetoothctl']
        print(f"\nSystem commands:")
        for cmd in system_deps:
            try:
                import subprocess
                result = subprocess.run(f"which {cmd}", shell=True, capture_output=True)
                status = "✅ OK" if result.returncode == 0 else "❌ Missing"
                print(f"{cmd:20} {status}")
            except:
                print(f"{cmd:20} ❌ Error checking")
        
        # Bluetooth permissions
        print(f"\nBluetooth permissions:")
        if os.geteuid() == 0:
            print("Root access:         ✅ Running as root")
        else:
            print("Root access:         ⚠️  Not running as root")
            print("                     💡 Some features may require sudo")
    
    def run_pytag_rich(self):
        """Run PyTAG with Rich UI"""
        if not MODULES_AVAILABLE:
            print("❌ PyTAG module not available")
            return
        
        print("\n🏷️  Starting PyTAG - AirTag Detector (Rich UI)")
        print("💡 Press Ctrl+C to return to main menu\n")
        time.sleep(2)
        
        try:
            run_pytag(simple_mode=False)
        except KeyboardInterrupt:
            print("\n🔙 Returning to main menu...")
        except Exception as e:
            print(f"❌ Error running PyTAG: {e}")
    
    def run_pytag_simple(self):
        """Run PyTAG in simple mode"""
        if not MODULES_AVAILABLE:
            print("❌ PyTAG module not available")
            return
        
        print("\n🏷️  Starting PyTAG - AirTag Detector (Simple mode)")
        print("💡 Press Ctrl+C to return to main menu\n")
        time.sleep(2)
        
        try:
            run_pytag(simple_mode=True)
        except KeyboardInterrupt:
            print("\n🔙 Returning to main menu...")
        except Exception as e:
            print(f"❌ Error running PyTAG: {e}")
    
    def run_wss_continuous(self):
        """Run WSS continuous scanning"""
        if not MODULES_AVAILABLE:
            print("❌ WSS module not available")
            return
        
        print("\n📡 Starting WSS - WiFi Scanner Suite (Continuous)")
        print("💡 Press Ctrl+C to return to main menu\n")
        time.sleep(2)
        
        try:
            run_wss_continuous()
        except KeyboardInterrupt:
            print("\n🔙 Returning to main menu...")
        except Exception as e:
            print(f"❌ Error running WSS: {e}")
    
    def run_wss_autoconnect(self):
        """Run WSS auto-connect"""
        if not MODULES_AVAILABLE:
            print("❌ WSS module not available")
            return
        
        print("\n🔄 Starting WSS - Auto-connect to open networks")
        print("💡 Press Ctrl+C to return to main menu\n")
        time.sleep(2)
        
        try:
            run_wss_autoconnect()
        except KeyboardInterrupt:
            print("\n🔙 Returning to main menu...")
        except Exception as e:
            print(f"❌ Error running WSS auto-connect: {e}")
    
    def run_wss_statistics(self):
        """Show WSS statistics"""
        if not MODULES_AVAILABLE:
            print("❌ WSS module not available")
            return
        
        print("\n📊 WSS Statistics")
        print("="*30)
        
        try:
            run_wss_statistics()
        except Exception as e:
            print(f"❌ Error showing WSS statistics: {e}")
    
    def run(self):
        """Main application loop"""
        # Show banner
        self.show_banner()
        
        if not MODULES_AVAILABLE:
            print("❌ Critical error: Security modules not available")
            print("💡 Please check the modules directory and dependencies")
            return
        
        while self.running:
            try:
                if RICH_AVAILABLE:
                    self.console.clear()
                
                self.show_main_menu()
                
                if RICH_AVAILABLE:
                    choice = Prompt.ask("\n[bold yellow]Select option[/bold yellow]", default="1")
                else:
                    choice = input("\nSelect option (1-7, q): ").strip()
                
                if choice == "1":
                    self.run_pytag_rich()
                elif choice == "2":
                    self.run_pytag_simple()
                elif choice == "3":
                    self.run_wss_continuous()
                elif choice == "4":
                    self.run_wss_autoconnect()
                elif choice == "5":
                    self.run_wss_statistics()
                elif choice == "6":
                    self.show_system_info()
                elif choice == "7":
                    self.check_dependencies()
                elif choice.lower() == "q":
                    print("\n👋 Thank you for using Unified Security Tools Suite!")
                    self.running = False
                else:
                    print("❌ Invalid choice. Please select 1-7 or 'q'")
                
                if choice != "q" and self.running:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Application terminated by user")
                self.running = False
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WBS - WiFi Bluetooth Suite | Unified Security Tools Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 wbs.py                    # Run interactive menu
  python3 wbs.py --pytag            # Run PyTAG directly
  python3 wbs.py --pytag --simple   # Run PyTAG in simple mode
  python3 wbs.py --wss              # Run WSS continuous scan
  
Components:
  PyTAG - Apple AirTag detector using BLE scanning
  WSS   - WiFi Scanner Suite for network analysis
        """
    )
    
    parser.add_argument(
        "--pytag",
        action="store_true",
        help="Run PyTAG directly (skip menu)"
    )
    
    parser.add_argument(
        "--wss",
        action="store_true",
        help="Run WSS continuous scan directly (skip menu)"
    )
    
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple mode (for PyTAG)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Unified Security Tools Suite 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Direct execution modes
    if args.pytag:
        if not MODULES_AVAILABLE:
            print("❌ PyTAG module not available")
            sys.exit(1)
        try:
            run_pytag(simple_mode=args.simple)
        except KeyboardInterrupt:
            print("\n👋 PyTAG stopped!")
        sys.exit(0)
    
    if args.wss:
        if not MODULES_AVAILABLE:
            print("❌ WSS module not available")
            sys.exit(1)
        try:
            run_wss_continuous()
        except KeyboardInterrupt:
            print("\n👋 WSS stopped!")
        sys.exit(0)
    
    # Interactive menu mode
    app = UnifiedSecurityApp()
    app.run()


if __name__ == "__main__":
    main()
