#!/usr/bin/env python3
"""
WSS Module - WiFi Scanner Suite
Author: OK2HSS
Version: 2.1.2

Integrated module for the Unified Security Tools Suite.
Features:
- Continuous WiFi scanning with BSSID display
- Auto-connect to open networks
- Network device discovery and MAC scanning
- Advanced log viewer with BSSID information
- Export to JSON with device data
"""

import subprocess
import json
import time
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from pathlib import Path

# Rich library for beautiful terminal interface
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  For better appearance install rich: pip install rich")

@dataclass
class WiFiNetwork:
    """WiFi network representation"""
    ssid: str
    security: str
    signal: int
    frequency: int
    band: str
    channel: Optional[int] = None
    bssid: Optional[str] = None
    rssi: Optional[int] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

        # Determine band based on frequency (MHz)
        if self.frequency and self.frequency > 0:
            if 2400 <= self.frequency <= 2500:
                self.band = "2.4GHz"
            elif 5000 <= self.frequency <= 6000:
                self.band = "5GHz"
            elif self.frequency >= 6000:
                self.band = "6GHz"
            else:
                self.band = "Unknown"
        else:
            self.band = "Unknown"

    @property
    def is_open(self) -> bool:
        """Returns True if network is open"""
        return not self.security or self.security.strip() == ""

    @property
    def signal_quality(self) -> str:
        """Returns text description of signal quality"""
        if self.signal >= 80:
            return "Excellent"
        elif self.signal >= 60:
            return "Good"
        elif self.signal >= 40:
            return "Weak"
        else:
            return "Very weak"

@dataclass
class NetworkDevice:
    """Network device representation"""
    ip_address: str
    mac_address: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class ConnectionAttempt:
    """Connection attempt representation"""
    ssid: str
    timestamp: str
    success: bool
    ip_address: Optional[str] = None
    error_message: Optional[str] = None
    band: Optional[str] = None
    signal: Optional[int] = None
    ping_success: Optional[bool] = None
    ping_stats: Optional[str] = None

class WiFiConfig:
    """Application configuration"""
    def __init__(self, config_file: str = "wifi_config.json"):
        self.config_file = Path(config_file)
        self.default_config = {
            "interface": "wlan0",
            "test_host": "8.8.8.8",
            "scan_interval": 10,
            "log_dir": "./wifi_logs",
            "max_log_age_days": 30,
            "ping_timeout": 5,
            "connection_timeout": 15,
            "auto_cleanup": True,
            "export_format": "json"
        }
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return {**self.default_config, **json.load(f)}
            except Exception as e:
                print(f"⚠️  Error loading configuration: {e}")

        return self.default_config.copy()

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value

class WiFiScanner:
    """Main class for WiFi scanning"""

    def __init__(self, config: WiFiConfig):
        self.config = config
        self.console = Console() if RICH_AVAILABLE else None
        self.log_dir = Path(self.config.get("log_dir"))
        self.log_dir.mkdir(exist_ok=True)

        # Lists for storing data
        self.discovered_networks: List[WiFiNetwork] = []
        self.connection_attempts: List[ConnectionAttempt] = []
        self.discovered_devices: List[NetworkDevice] = []

    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
        """Execute system command"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    def check_dependencies(self) -> bool:
        """Check system dependencies"""
        dependencies = ['nmcli', 'ping', 'iwconfig']
        missing = []

        for dep in dependencies:
            success, _ = self.run_command(f"which {dep}")
            if not success:
                missing.append(dep)

        if missing:
            print(f"❌ Missing dependencies: {', '.join(missing)}")
            return False

        return True
    
    def scan_networks(self) -> List[WiFiNetwork]:
        """Scan available WiFi networks"""
        # Start rescan
        self.run_command("nmcli device wifi rescan", timeout=15)
        time.sleep(2)

        # Get network list with detailed information
        # First try to get RSSI with iwlist, fallback to nmcli
        rssi_data = {}
        rssi_success, rssi_output = self.run_command(
            f"iwlist {self.config.get('interface')} scan | grep -E 'ESSID|Signal level'"
        )

        if rssi_success:
            current_ssid = None
            for line in rssi_output.split('\n'):
                if 'ESSID:' in line:
                    current_ssid = line.split('ESSID:')[1].strip().strip('"')
                elif 'Signal level=' in line and current_ssid:
                    try:
                        rssi = int(line.split('Signal level=')[1].split(' ')[0])
                        rssi_data[current_ssid] = rssi
                    except:
                        pass

        # Get basic network list from nmcli
        success, output = self.run_command(
            "nmcli -t -f SSID,SECURITY,SIGNAL,FREQ,BSSID,CHAN device wifi list"
        )

        if not success:
            return []

        networks = []
        for line in output.strip().split('\n'):
            # Use robust parsing method
            parsed_data = self._parse_nmcli_line_robust(line)
            if not parsed_data:
                continue

            ssid = parsed_data['ssid']
            if not ssid:  # Skip empty SSID
                continue

            # Get RSSI if available
            rssi = rssi_data.get(ssid, None)

            network = WiFiNetwork(
                ssid=ssid,
                security=parsed_data['security'],
                signal=parsed_data['signal'],
                frequency=parsed_data['frequency'],
                band="Unknown",  # Will be determined in __post_init__
                channel=parsed_data['channel'],
                bssid=parsed_data['bssid'],
                rssi=rssi
            )
            networks.append(network)

        # Add only new networks to discovered networks list (deduplicate by SSID+BSSID)
        self._add_unique_networks(networks)
        return networks

    def _add_unique_networks(self, new_networks: List[WiFiNetwork]):
        """Add only unique networks to discovered_networks list"""
        # Create a set of existing network identifiers (SSID + BSSID combination)
        existing_networks = set()
        for network in self.discovered_networks:
            # Use SSID + BSSID as unique identifier (BSSID is MAC address of access point)
            identifier = f"{network.ssid}|{network.bssid or 'no_bssid'}"
            existing_networks.add(identifier)

        # Add only networks that don't already exist
        for network in new_networks:
            identifier = f"{network.ssid}|{network.bssid or 'no_bssid'}"
            if identifier not in existing_networks:
                self.discovered_networks.append(network)
                existing_networks.add(identifier)  # Update set for next iterations

    def _validate_bssid(self, bssid: str) -> Optional[str]:
        """Validate and clean BSSID format"""
        if not bssid:
            return None

        # Remove any escape characters or extra backslashes
        bssid = bssid.replace('\\', '').strip()

        # Check if it's a valid MAC address format
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if mac_pattern.match(bssid):
            return bssid.upper()  # Normalize to uppercase

        # Check if it's a partial MAC (just first part)
        partial_pattern = re.compile(r'^[0-9A-Fa-f]{2}$')
        if partial_pattern.match(bssid):
            # This is likely a parsing error - return None to indicate invalid
            return None

        return None

    def _parse_nmcli_line_robust(self, line: str) -> Optional[dict]:
        """Robustly parse nmcli output line with proper BSSID handling"""
        if not line.strip():
            return None

        # Split by colon, but be smart about BSSID
        parts = line.split(':')

        # We expect at least SSID:SECURITY:SIGNAL:FREQ:BSSID_PART1:...:BSSID_PART6:CHAN
        # That's minimum 8 parts (SSID, SECURITY, SIGNAL, FREQ, 6 BSSID parts, CHAN)
        if len(parts) < 8:
            return None

        try:
            ssid = parts[0].strip()
            security = parts[1].strip()
            signal_str = parts[2].strip()
            freq_str = parts[3].strip()

            # Reconstruct BSSID from parts[4] to parts[9] (6 parts)
            bssid_parts = parts[4:10]  # Take 6 parts for BSSID
            bssid_raw = ':'.join(bssid_parts)

            # Channel is the part after BSSID
            channel_str = parts[10] if len(parts) > 10 else ""

            # Validate and clean BSSID
            bssid = self._validate_bssid(bssid_raw)

            # Parse signal
            signal = int(signal_str) if signal_str.isdigit() else 0

            # Parse frequency
            freq = self._parse_frequency(freq_str)

            # Parse channel
            channel = self._parse_channel(channel_str, freq)

            return {
                'ssid': ssid,
                'security': security,
                'signal': signal,
                'frequency': freq,
                'bssid': bssid,
                'channel': channel
            }

        except (ValueError, IndexError) as e:
            # Log parsing error for debugging
            print(f"⚠️  Parsing error for line: {line[:50]}... - {e}")
            return None

    def _parse_frequency(self, freq_str: str) -> int:
        """Parse frequency string to MHz"""
        if not freq_str:
            return 0

        try:
            # Clean frequency string
            freq_clean = freq_str.replace('MHz', '').replace('GHz', '').replace(' ', '').strip()

            if '.' in freq_clean:
                # Handle "2.412" format (GHz) - convert to MHz
                return int(float(freq_clean) * 1000)
            else:
                # Handle "2412" format (MHz)
                return int(freq_clean)
        except ValueError:
            return 0

    def _parse_channel(self, channel_str: str, frequency: int) -> Optional[int]:
        """Parse channel number with frequency-based fallback"""
        # Try direct parsing first
        if channel_str and channel_str.isdigit():
            return int(channel_str)

        # Fallback: calculate channel from frequency
        if frequency > 0:
            return self._frequency_to_channel(frequency)

        return None

    def _frequency_to_channel(self, frequency: int) -> Optional[int]:
        """Convert frequency to WiFi channel number"""
        # 2.4GHz band channels
        if 2412 <= frequency <= 2484:
            if frequency == 2484:
                return 14
            else:
                return (frequency - 2412) // 5 + 1

        # 5GHz band channels (simplified mapping)
        elif 5000 <= frequency <= 6000:
            # Common 5GHz channels
            freq_to_chan_5g = {
                5180: 36, 5200: 40, 5220: 44, 5240: 48,
                5260: 52, 5280: 56, 5300: 60, 5320: 64,
                5500: 100, 5520: 104, 5540: 108, 5560: 112,
                5580: 116, 5600: 120, 5620: 124, 5640: 128,
                5660: 132, 5680: 136, 5700: 140, 5720: 144,
                5745: 149, 5765: 153, 5785: 157, 5805: 161,
                5825: 165
            }
            return freq_to_chan_5g.get(frequency)

        return None

    def continuous_scan(self):
        """Continuous scanning"""
        if not RICH_AVAILABLE:
            return self._continuous_scan_simple()

        return self._continuous_scan_rich()

    def _continuous_scan_simple(self):
        """Simple continuous scanning without rich"""
        scan_count = 0
        try:
            while True:
                scan_count += 1
                print(f"\n{'='*50}")
                print(f"Scan #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*50}")

                networks = self.scan_networks()
                open_networks = [n for n in networks if n.is_open]

                band_24_simple = [n for n in networks if n.band == "2.4GHz"]
                band_5_simple = [n for n in networks if n.band == "5GHz"]
                band_6_simple = [n for n in networks if n.band == "6GHz"]

                print(f"📡 Total networks: {len(networks)}")
                print(f"🔓 Open networks: {len(open_networks)}")
                print(f"📡 2.4GHz: {len(band_24_simple)}")
                print(f"⚡ 5GHz: {len(band_5_simple)}")
                print(f"🚀 6GHz: {len(band_6_simple)}")

                if open_networks:
                    print("\n🎉 OPEN NETWORKS FOUND:")
                    for net in open_networks:
                        band_display = net.band if net.band else "Unknown"
                        rssi_display = f" ({net.rssi}dBm)" if net.rssi else ""
                        bssid_display = f" | BSSID: {net.bssid}" if net.bssid else ""
                        print(f"  → \033[92m{net.ssid}\033[0m ({net.signal}%{rssi_display} {band_display}){bssid_display} \033[92m[OPEN]\033[0m")

                print(f"\nWaiting {self.config.get('scan_interval')}s...")
                time.sleep(self.config.get('scan_interval'))

        except KeyboardInterrupt:
            print("\n\nScanning terminated by user.")

    def _continuous_scan_rich(self):
        """Advanced continuous scanning with rich"""
        scan_count = 0

        try:
            while True:
                scan_count += 1

                # Scanning
                with self.console.status("[bold green]Scanning WiFi networks..."):
                    networks = self.scan_networks()

                # Statistics
                open_networks = [n for n in networks if n.is_open]
                band_24 = [n for n in networks if n.band == "2.4GHz"]
                band_5 = [n for n in networks if n.band == "5GHz"]
                band_6 = [n for n in networks if n.band == "6GHz"]
                unknown_bands = [n for n in networks if n.band.startswith("Unknown")]

                # Create table
                table = Table(title=f"WiFi Scan #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                table.add_column("SSID", style="cyan")
                table.add_column("Security")
                table.add_column("Signal", style="green")
                table.add_column("Band", style="magenta")
                table.add_column("BSSID", style="dim")
                table.add_column("Quality", style="yellow")

                # Sort by signal strength
                networks_sorted = sorted(networks, key=lambda x: x.signal, reverse=True)

                for network in networks_sorted[:15]:  # Show only top 15
                    # Color coding for security
                    if network.is_open:
                        security_display = "[bold green]🔓 OPEN[/bold green]"
                        ssid_style = "[bold green]"
                        ssid_display = f"{ssid_style}{network.ssid}[/bold green]"
                    else:
                        security_display = f"[red]🔒 {network.security}[/red]"
                        ssid_display = network.ssid

                    # Enhanced signal display with RSSI
                    if network.rssi:
                        signal_display = f"{network.signal}% ({network.rssi}dBm)"
                    else:
                        signal_display = f"{network.signal}%"

                    band_display = network.band if network.band else "Unknown"
                    bssid_display = network.bssid if network.bssid else "N/A"

                    table.add_row(
                        ssid_display,
                        security_display,
                        signal_display,
                        band_display,
                        bssid_display,
                        network.signal_quality
                    )

                # Statistics panel
                stats_text = f"""
📊 [bold]Statistics:[/bold]
  • Total networks: [bold blue]{len(networks)}[/bold blue]
  • 🔓 Open: [bold green]{len(open_networks)}[/bold green]
  • 📡 2.4GHz: [bold cyan]{len(band_24)}[/bold cyan]
  • ⚡ 5GHz: [bold magenta]{len(band_5)}[/bold magenta]
  • 🚀 6GHz: [bold yellow]{len(band_6)}[/bold yellow]
"""

                if unknown_bands:
                    stats_text += f"  • ❓ Unknown: [bold red]{len(unknown_bands)}[/bold red]\n"

                if open_networks:
                    stats_text += f"\n🎉 [bold yellow]FOUND {len(open_networks)} OPEN NETWORKS![/bold yellow]"

                stats_panel = Panel(stats_text, title="📈 Overview", border_style="green")

                # Display
                self.console.clear()
                self.console.print(table)
                self.console.print(stats_panel)

                # Progress bar countdown
                scan_interval = self.config.get('scan_interval')
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Waiting for next scan..."),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task("countdown", total=scan_interval)
                    for _ in range(scan_interval):
                        time.sleep(1)
                        progress.update(task, advance=1)

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Scanning terminated by user.[/yellow]")

    def auto_connect(self):
        """Automatic connection to open networks"""
        if RICH_AVAILABLE:
            self.console.print("[bold cyan]🔍 Scanning for WiFi networks...[/bold cyan]")
        else:
            print("🔍 Scanning for WiFi networks...")

        networks = self.scan_networks()
        open_networks = [n for n in networks if n.is_open]

        if not open_networks:
            if RICH_AVAILABLE:
                self.console.print("[red]❌ No open networks found[/red]")
            else:
                print("❌ No open networks found")
            return

        # Sort by signal strength
        open_networks.sort(key=lambda x: x.signal, reverse=True)

        if RICH_AVAILABLE:
            self.console.print(f"[green]🔍 Found {len(open_networks)} open networks[/green]")

            # Show available networks
            self.console.print("\n[bold]Available open networks:[/bold]")
            for i, net in enumerate(open_networks[:5], 1):
                rssi_info = f" ({net.rssi}dBm)" if net.rssi else ""
                self.console.print(f"  {i}. [green]{net.ssid}[/green] - {net.signal}%{rssi_info} [{net.band}]")
        else:
            print(f"🔍 Found {len(open_networks)} open networks")
            print("\nAvailable open networks:")
            for i, net in enumerate(open_networks[:5], 1):
                rssi_info = f" ({net.rssi}dBm)" if net.rssi else ""
                print(f"  {i}. {net.ssid} - {net.signal}%{rssi_info} [{net.band}]")

        print()  # Empty line for better readability

        for i, network in enumerate(open_networks, 1):
            # Show which network we're trying
            if RICH_AVAILABLE:
                self.console.print(f"[bold blue]🔄 [{i}/{len(open_networks)}] Attempting to connect to: [cyan]{network.ssid}[/cyan][/bold blue]")
                self.console.print(f"   Signal: {network.signal}% | Band: {network.band} | BSSID: {network.bssid or 'N/A'}")
            else:
                print(f"🔄 [{i}/{len(open_networks)}] Attempting to connect to: {network.ssid}")
                print(f"   Signal: {network.signal}% | Band: {network.band} | BSSID: {network.bssid or 'N/A'}")

            # Here would be connection attempt logic - simplified for module
            print("   ⚠️  Connection testing disabled in module mode")
            print()  # Empty line between attempts


class WiFiScannerApp:
    """Main application with menu"""

    def __init__(self, show_banner=False):
        self.config = WiFiConfig()
        self.scanner = WiFiScanner(self.config)
        self.console = Console() if RICH_AVAILABLE else None

    def run_continuous_scan(self):
        """Run continuous scanning"""
        return self.scanner.continuous_scan()

    def run_auto_connect(self):
        """Run auto-connect"""
        return self.scanner.auto_connect()

    def show_statistics(self):
        """Show statistics"""
        if not self.scanner.discovered_networks:
            print("❌ No data to analyze")
            return

        open_networks = [n for n in self.scanner.discovered_networks if n.is_open]

        if RICH_AVAILABLE:
            table = Table(title="📊 WiFi Scanner Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total scanned networks", str(len(self.scanner.discovered_networks)))
            table.add_row("Open networks", str(len(open_networks)))

            self.console.print(table)
        else:
            print(f"📊 Statistics:")
            print(f"  • Total networks: {len(self.scanner.discovered_networks)}")
            print(f"  • Open networks: {len(open_networks)}")


def run_wss_continuous():
    """Run WSS continuous scanning from unified app"""
    if not RICH_AVAILABLE:
        print("⚠️  Rich library not available, using simple mode")

    app = WiFiScannerApp()

    if not app.scanner.check_dependencies():
        print("❌ Missing system dependencies")
        return False

    try:
        app.run_continuous_scan()
        return True
    except KeyboardInterrupt:
        print("\n👋 WSS scanning stopped!")
        return True
    except Exception as e:
        print(f"❌ Error running WSS: {e}")
        return False


def run_wss_autoconnect():
    """Run WSS auto-connect from unified app"""
    if not RICH_AVAILABLE:
        print("⚠️  Rich library not available, using simple mode")

    app = WiFiScannerApp()

    if not app.scanner.check_dependencies():
        print("❌ Missing system dependencies")
        return False

    try:
        app.run_auto_connect()
        return True
    except KeyboardInterrupt:
        print("\n👋 WSS auto-connect stopped!")
        return True
    except Exception as e:
        print(f"❌ Error running WSS auto-connect: {e}")
        return False


def run_wss_statistics():
    """Show WSS statistics from unified app"""
    app = WiFiScannerApp()

    try:
        app.show_statistics()
        return True
    except Exception as e:
        print(f"❌ Error showing WSS statistics: {e}")
        return False
