#!/usr/bin/env python3
"""
PyTAG Module - Python AirTag Detector
Author: OK2HSS
Version: 1.0.0

Integrated module for the Unified Security Tools Suite.
Detects Apple AirTags using Bluetooth Low Energy (BLE) scanning.
"""

import asyncio
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import sys
import os

try:
    from bleak import BleakScanner, BleakError
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("📦 Install with: pip install bleak rich")
    RICH_AVAILABLE = False


@dataclass
class AirTagDevice:
    """Represents a detected AirTag device"""
    address: str
    rssi: int
    distance: float
    trend: str  # "red", "green", "blue"
    count: int
    last_seen: datetime
    details: str


class AirTagDetector:
    """Main AirTag detection class"""
    
    def __init__(self):
        self.detected_airtags: Dict[str, AirTagDevice] = {}
        self.airtags_lock = threading.Lock()
        self.console = Console() if RICH_AVAILABLE else None
        self.scanning = False
        self.scan_count = 0
        
        # Configuration
        self.tx_power = -59  # Typical value for 1 meter
        self.device_timeout = 60  # Seconds to keep device in list
        self.scan_interval = 1.0  # Seconds between scans
        
    def calculate_distance(self, rssi: int) -> float:
        """Calculate approximate distance based on RSSI"""
        if rssi == 0:
            return -1.0
            
        ratio = rssi * 1.0 / self.tx_power
        if ratio < 1.0:
            return pow(ratio, 10)
        else:
            return (0.89976) * pow(ratio, 7.7095) + 0.111
    
    def get_trend_color(self, trend: str) -> str:
        """Get color for trend display"""
        colors = {
            "red": "red",      # Signal increasing
            "green": "green",  # Signal stable  
            "blue": "blue"     # Signal decreasing
        }
        return colors.get(trend, "white")
    
    def get_trend_symbol(self, trend: str) -> str:
        """Get symbol for trend display"""
        symbols = {
            "red": "↗",    # Increasing
            "green": "→",  # Stable
            "blue": "↘"    # Decreasing
        }
        return symbols.get(trend, "→")

    def is_airtag(self, apple_data: bytes) -> bool:
        """Check if Apple manufacturer data indicates an AirTag"""
        if len(apple_data) < 2:
            return False

        # Check for AirTag specific payload types
        payload_type = apple_data[0]

        # Registered AirTag (connected to FindMy network)
        if payload_type == 0x12:
            # Should have length 0x19 (25 bytes) and status byte 0x10
            if len(apple_data) >= 3:
                payload_length = apple_data[1]
                if payload_length == 0x19 and len(apple_data) >= 4:
                    status_byte = apple_data[2]
                    # Status byte 0x10 indicates AirTag in normal operation
                    return status_byte == 0x10

        # Unregistered AirTag (not yet connected to FindMy network)
        elif payload_type == 0x07:
            # Should have length 0x19 (25 bytes)
            if len(apple_data) >= 2:
                payload_length = apple_data[1]
                return payload_length == 0x19

        return False
    
    def detection_callback(self, device, advertisement_data):
        """Callback function for BLE device detection"""
        address = device.address
        rssi = advertisement_data.rssi
        
        # Check for Apple manufacturer data (0x004C)
        manufacturer_data = advertisement_data.manufacturer_data
        if not manufacturer_data:
            return
            
        # Look for Apple manufacturer ID (0x004C = 76 decimal)
        apple_data = manufacturer_data.get(76)  # 0x004C in decimal
        if not apple_data:
            return
            
        # Debug: Store Apple device info for batch display
        if len(apple_data) >= 2:
            payload_type = apple_data[0]
            payload_length = apple_data[1] if len(apple_data) > 1 else 0
            debug_info = f"{address} | Type: 0x{payload_type:02x} | Length: 0x{payload_length:02x} | Data: {apple_data.hex()}"

            # Add to debug buffer (limit to last 10 entries)
            if not hasattr(self, 'debug_buffer'):
                self.debug_buffer = []
            self.debug_buffer.append(debug_info)
            if len(self.debug_buffer) > 10:
                self.debug_buffer.pop(0)

        # Check if this is actually an AirTag based on advertising data structure
        if not self.is_airtag(apple_data):
            return
            
        # Calculate distance
        distance = self.calculate_distance(rssi)
        
        # Build device details
        details = f"RSSI: {rssi}dBm | Distance: {distance:.2f}m"
        if device.name:
            details += f" | Name: {device.name}"
        
        # Update device information with thread safety
        with self.airtags_lock:
            current_time = datetime.now(timezone.utc)
            
            if address in self.detected_airtags:
                # Update existing device
                old_device = self.detected_airtags[address]
                
                # Calculate trend based on RSSI change
                if rssi > old_device.rssi:
                    trend = "red"    # Signal increasing (getting closer)
                elif rssi < old_device.rssi:
                    trend = "blue"   # Signal decreasing (getting farther)
                else:
                    trend = "green"  # Signal stable
                
                # Update device
                self.detected_airtags[address] = AirTagDevice(
                    address=address,
                    rssi=rssi,
                    distance=distance,
                    trend=trend,
                    count=old_device.count + 1,
                    last_seen=current_time,
                    details=details
                )
            else:
                # New device
                self.detected_airtags[address] = AirTagDevice(
                    address=address,
                    rssi=rssi,
                    distance=distance,
                    trend="green",  # Default to stable for new devices
                    count=1,
                    last_seen=current_time,
                    details=details
                )
    
    def cleanup_stale_devices(self):
        """Remove devices that haven't been seen recently"""
        with self.airtags_lock:
            current_time = datetime.now(timezone.utc)
            timeout_threshold = current_time - timedelta(seconds=self.device_timeout)
            
            # Find stale devices
            stale_addresses = [
                addr for addr, device in self.detected_airtags.items()
                if device.last_seen < timeout_threshold
            ]
            
            # Remove stale devices
            for addr in stale_addresses:
                del self.detected_airtags[addr]
    
    def create_display_table(self) -> Table:
        """Create Rich table for displaying AirTags"""
        table = Table(
            title="🏷️  Detected AirTags",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        # Add columns
        table.add_column("Address", style="cyan", no_wrap=True)
        table.add_column("RSSI", justify="right", style="yellow")
        table.add_column("Distance", justify="right", style="green")
        table.add_column("Trend", justify="center", style="white")
        table.add_column("Count", justify="right", style="blue")
        table.add_column("Last Seen", style="dim")
        
        # Add rows with thread safety
        with self.airtags_lock:
            devices_copy = dict(self.detected_airtags)
        
        if not devices_copy:
            table.add_row("No AirTags detected", "", "", "", "", "")
            return table
        
        # Sort by RSSI (strongest signal first)
        sorted_devices = sorted(
            devices_copy.items(),
            key=lambda x: x[1].rssi,
            reverse=True
        )
        
        for address, device in sorted_devices:
            # Format last seen time
            time_diff = datetime.now(timezone.utc) - device.last_seen
            if time_diff.total_seconds() < 60:
                last_seen = f"{int(time_diff.total_seconds())}s ago"
            else:
                last_seen = f"{int(time_diff.total_seconds() / 60)}m ago"
            
            # Get trend color and symbol
            trend_color = self.get_trend_color(device.trend)
            trend_symbol = self.get_trend_symbol(device.trend)
            
            table.add_row(
                device.address,
                f"{device.rssi}dBm",
                f"{device.distance:.2f}m",
                Text(trend_symbol, style=trend_color),
                str(device.count),
                last_seen
            )
        
        return table
    
    def create_status_panel(self) -> Panel:
        """Create status information panel"""
        status_text = f"""
🔍 Scanning Status: {'🟢 Active' if self.scanning else '🔴 Stopped'}
📊 Scan Count: {self.scan_count}
🏷️  AirTags Found: {len(self.detected_airtags)}
⏰ Device Timeout: {self.device_timeout}s
🔄 Scan Interval: {self.scan_interval}s

💡 Press Ctrl+C to stop scanning
        """.strip()

        return Panel(
            status_text,
            title="📡 PyTAG Status",
            border_style="blue"
        )

    def create_ble_activity_panel(self) -> Panel:
        """Create BLE activity panel"""
        if hasattr(self, 'debug_buffer') and self.debug_buffer:
            activity_text = "\n".join(self.debug_buffer[-8:])  # Show last 8 entries
        else:
            activity_text = "Waiting for BLE activity..."

        return Panel(
            activity_text,
            title="🔍 BLE Communication Activity",
            border_style="yellow",
            height=12
        )

    async def scanner_loop(self):
        """Main BLE scanning loop with auto-restart capability"""
        while self.scanning:
            try:
                if self.console:
                    self.console.print("🔍 Starting BLE scanner...", style="green")
                else:
                    print("🔍 Starting BLE scanner...")

                scanner = BleakScanner(detection_callback=self.detection_callback)

                await scanner.start()

                # Keep scanning until stopped
                while self.scanning:
                    await asyncio.sleep(self.scan_interval)
                    self.scan_count += 1

                    # Cleanup stale devices periodically
                    if self.scan_count % 30 == 0:  # Every 30 scans
                        self.cleanup_stale_devices()

                await scanner.stop()

            except BleakError as e:
                if self.console:
                    self.console.print(f"❌ BLEAK ERROR: {e}", style="red")
                    self.console.print("🔄 Restarting scanner in 5 seconds...", style="yellow")
                else:
                    print(f"❌ BLEAK ERROR: {e}")
                    print("🔄 Restarting scanner in 5 seconds...")
                await asyncio.sleep(5)

            except Exception as e:
                if self.console:
                    self.console.print(f"❌ UNEXPECTED ERROR: {e}", style="red")
                    self.console.print("🔄 Restarting scanner in 15 seconds...", style="yellow")
                else:
                    print(f"❌ UNEXPECTED ERROR: {e}")
                    print("🔄 Restarting scanner in 15 seconds...")
                await asyncio.sleep(15)

    def start_scanner_thread(self):
        """Start the BLE scanner in a separate thread"""
        def run_scanner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.scanner_loop())
            finally:
                loop.close()

        scanner_thread = threading.Thread(target=run_scanner, daemon=True)
        scanner_thread.start()
        return scanner_thread

    def run_cli_interface(self):
        """Run the CLI interface with live updates"""
        if not RICH_AVAILABLE:
            return self.run_simple_mode()

        self.scanning = True

        # Start scanner in background thread
        scanner_thread = self.start_scanner_thread()

        try:
            # Create layout with three sections
            layout = Layout()
            layout.split_column(
                Layout(name="status", size=10),
                Layout(name="ble_activity", size=14),
                Layout(name="airtags")
            )

            with Live(layout, refresh_per_second=2, screen=True) as live:
                while self.scanning:
                    try:
                        # Update layout
                        layout["status"].update(self.create_status_panel())
                        layout["ble_activity"].update(self.create_ble_activity_panel())
                        layout["airtags"].update(self.create_display_table())

                        time.sleep(0.5)  # Update every 500ms

                    except KeyboardInterrupt:
                        break

        except KeyboardInterrupt:
            pass
        finally:
            self.scanning = False
            if self.console:
                self.console.print("\n🛑 Stopping scanner...", style="yellow")
            else:
                print("\n🛑 Stopping scanner...")

            # Wait for scanner thread to finish
            scanner_thread.join(timeout=5)

            if self.console:
                self.console.print("✅ PyTAG stopped successfully!", style="green")
            else:
                print("✅ PyTAG stopped successfully!")

    def run_simple_mode(self):
        """Run in simple mode without Rich UI"""
        self.scanning = True

        # Start scanner in background thread
        scanner_thread = self.start_scanner_thread()

        try:
            print("🔍 PyTAG - AirTag Detector Started")
            print("💡 Press Ctrl+C to stop\n")

            while self.scanning:
                try:
                    # Clear screen (simple)
                    os.system('clear' if os.name == 'posix' else 'cls')

                    # Compact header
                    print("🔍 PyTAG - AirTag Detector")
                    print(f"📊 Scans: {self.scan_count} | AirTags: {len(self.detected_airtags)}")
                    print("=" * 80)

                    # Split screen layout - BLE Activity (left) and AirTags (right)
                    ble_lines = []
                    airtag_lines = []

                    # Prepare BLE Activity lines (left column) - reduced
                    ble_lines.append("🔍 BLE Activity:")
                    ble_lines.append("-" * 38)
                    if hasattr(self, 'debug_buffer') and self.debug_buffer:
                        for debug_line in self.debug_buffer[-4:]:  # Show last 4 only
                            # Truncate long lines to fit column
                            if len(debug_line) > 36:
                                ble_lines.append(f"{debug_line[:33]}...")
                            else:
                                ble_lines.append(debug_line)
                    else:
                        ble_lines.append("Waiting for BLE activity...")

                    # Pad BLE lines to smaller height
                    while len(ble_lines) < 8:
                        ble_lines.append("")

                    # Prepare AirTag lines (right column) - expanded
                    airtag_lines.append("🏷️  AirTag Detection Results:")
                    airtag_lines.append("-" * 38)

                    with self.airtags_lock:
                        devices_copy = dict(self.detected_airtags)

                    if devices_copy:
                        # Sort by RSSI (strongest signal first)
                        sorted_devices = sorted(
                            devices_copy.items(),
                            key=lambda x: x[1].rssi,
                            reverse=True
                        )

                        airtag_lines.append("┌─ DETECTED AIRTAGS ─────────────┐")
                        airtag_lines.append(f"│ Found: {len(devices_copy)} AirTag(s)")
                        airtag_lines.append("├────────────────────────────────┤")

                        for i, (address, device) in enumerate(sorted_devices[:3]):  # Show max 3 AirTags
                            # Format last seen time
                            time_diff = datetime.now(timezone.utc) - device.last_seen
                            if time_diff.total_seconds() < 60:
                                last_seen = f"{int(time_diff.total_seconds())}s"
                            else:
                                last_seen = f"{int(time_diff.total_seconds() // 60)}m"

                            trend_symbol = self.get_trend_symbol(device.trend)

                            # Detailed display for each AirTag
                            airtag_lines.append(f"│ 📍 {address[:17]}")
                            airtag_lines.append(f"│ 📶 RSSI: {device.rssi} dBm")
                            airtag_lines.append(f"│ 📏 Distance: {device.distance:.1f}m {trend_symbol}")
                            airtag_lines.append(f"│ 📊 Detections: {device.count}")
                            airtag_lines.append(f"│ 🕐 Last seen: {last_seen} ago")
                            if i < len(sorted_devices) - 1 and i < 2:  # Add separator
                                airtag_lines.append("├────────────────────────────────┤")

                        airtag_lines.append("└────────────────────────────────┘")
                    else:
                        airtag_lines.append("┌─ AIRTAG STATUS ────────────────┐")
                        airtag_lines.append("│                                │")
                        airtag_lines.append("│        No AirTags found        │")
                        airtag_lines.append("│                                │")
                        airtag_lines.append("│     🔍 Monitoring active...    │")
                        airtag_lines.append("│                                │")
                        airtag_lines.append("│   ✅ Expected if none nearby   │")
                        airtag_lines.append("│                                │")
                        airtag_lines.append("└────────────────────────────────┘")

                    # Pad AirTag lines to larger height for more space
                    while len(airtag_lines) < 15:
                        airtag_lines.append("")

                    # Print side-by-side layout with more lines
                    print()
                    for i in range(15):
                        ble_part = ble_lines[i] if i < len(ble_lines) else ""
                        airtag_part = airtag_lines[i] if i < len(airtag_lines) else ""

                        # Format with fixed widths (38 chars each + separator)
                        print(f"{ble_part:<38} | {airtag_part}")

                    print("\n💡 Press Ctrl+C to stop scanning")

                    time.sleep(2)  # Update every 2 seconds

                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            pass
        finally:
            self.scanning = False
            print("\n🛑 Stopping scanner...")

            # Wait for scanner thread to finish
            scanner_thread.join(timeout=5)

            print("✅ PyTAG stopped successfully!")


def check_bluetooth_permissions():
    """Check if we have proper Bluetooth permissions"""
    if os.geteuid() != 0:
        print("⚠️  Warning: Running without root privileges")
        print("💡 If scanning fails, try:")
        print("   sudo python3 main.py")
        print("   or")
        print("   sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)")
        print()


def run_pytag(simple_mode=False, timeout=60, interval=1.0):
    """Main function to run PyTAG from the unified app"""
    if not RICH_AVAILABLE:
        print("❌ Missing required dependencies for PyTAG")
        print("📦 Install with: pip install bleak rich")
        return

    # Check Bluetooth permissions
    check_bluetooth_permissions()

    # Create detector instance
    detector = AirTagDetector()
    detector.device_timeout = timeout
    detector.scan_interval = interval

    try:
        if simple_mode:
            detector.run_simple_mode()
        else:
            detector.run_cli_interface()
    except KeyboardInterrupt:
        print("\n👋 PyTAG stopped!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return False

    return True
