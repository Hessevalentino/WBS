# Unified Security Tools Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/Hessevalentino/WBS.svg)](https://github.com/Hessevalentino/WBS/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/Hessevalentino/WBS.svg)](https://github.com/Hessevalentino/WBS/issues)

🛡️ **Profesionální bezpečnostní nástroje v jedné aplikaci**

Sjednocená aplikace kombinující dva výkonné bezpečnostní nástroje:
- **🏷️ PyTAG** - Detektor Apple AirTagů pomocí BLE skenování
- **📡 WSS** - WiFi Scanner Suite pro analýzu bezdrátových sítí

## 🎯 Funkce

### PyTAG - AirTag Detector
- ✅ **Real-time BLE skenování** - Kontinuální sledování Apple AirTagů
- 📊 **RSSI trend analýza** - Vizuální indikátory změn síly signálu
- 📏 **Odhad vzdálenosti** - Aproximace vzdálenosti na základě RSSI
- 🎨 **Dva režimy zobrazení** - Rich UI a Simple mode
- 🔍 **Debug informace** - Analýza BLE advertising dat

### WSS - WiFi Scanner Suite
- 📡 **Kontinuální WiFi skenování** - S BSSID informacemi
- 🔄 **Auto-připojení** - K otevřeným sítím
- 🖥️ **Detekce síťových zařízení** - MAC scanning
- 📊 **Pokročilý log viewer** - S BSSID informacemi
- 💾 **Export do JSON** - S daty o zařízeních

## 🚀 Rychlé spuštění

### 1. Instalace závislostí

```bash
# Přejděte do složky app
cd app

# Vytvořte virtuální prostředí (doporučeno)
python3 -m venv venv
source venv/bin/activate

# Instalujte Python závislosti
pip install -r requirements.txt

# Instalujte systémové závislosti (Ubuntu/Debian)
sudo apt update
sudo apt install bluetooth bluez network-manager wireless-tools
```

### 2. Spuštění aplikace

```bash
# Interaktivní menu (doporučeno)
python3 wbs.py

# Nebo s root oprávněními pro lepší funkcionalitu
sudo python3 wbs.py

# Nebo pomocí run.sh (automaticky nastaví venv)
./run.sh
```

## 📖 Způsoby použití

### Interaktivní menu
```bash
python3 wbs.py
# nebo
./run.sh
```
Zobrazí hlavní menu s možnostmi:
1. 🏷️ PyTAG (Rich UI)
2. 🏷️ PyTAG (Simple mode)
3. 📡 WSS Continuous scanning
4. 🔄 WSS Auto-connect
5. 📊 WSS Statistics
6. ℹ️ System information
7. ⚙️ Check dependencies

### Přímé spuštění
```bash
# PyTAG s Rich UI
python3 wbs.py --pytag
./run.sh --pytag

# PyTAG v simple módu
python3 wbs.py --pytag --simple
./run.sh --pytag-simple

# WSS continuous scanning
python3 wbs.py --wss
./run.sh --wss
```

### Příklady s parametry
```bash
# Zobrazit nápovědu
python3 wbs.py --help

# Zobrazit verzi
python3 wbs.py --version
```

## 🔧 Systémové požadavky

### Základní požadavky
- **Python 3.8+**
- **Linux** (testováno na Ubuntu/Debian)
- **Bluetooth adaptér** s BLE podporou (pro PyTAG)
- **WiFi adaptér** (pro WSS)

### Doporučené oprávnění
```bash
# Pro PyTAG (BLE přístup)
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)

# Nebo spusťte jako root
sudo python3 wbs.py
sudo ./run.sh
```

## 📊 Rozhraní aplikace

### Hlavní menu (Rich UI)
```
╔══════════════════════════════════════════════════════════════════════════════╗
║  🛡️  Unified Security Tools Suite                                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PyTAG - AirTag Detector:                                                    ║
║    1. 🏷️  Run PyTAG (Rich UI)                                               ║
║    2. 🏷️  Run PyTAG (Simple mode)                                           ║
║                                                                              ║
║  WSS - WiFi Scanner Suite:                                                   ║
║    3. 📡 Continuous WiFi scanning                                           ║
║    4. 🔄 Auto-connect to open networks                                      ║
║    5. 📊 Show WiFi statistics                                               ║
║                                                                              ║
║  System:                                                                     ║
║    6. ℹ️  Show system information                                           ║
║    7. ⚙️  Check dependencies                                                ║
║    q. ❌ Exit application                                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### PyTAG - Detekce AirTagů
```
┌─────────────────── 📡 PyTAG Status ───────────────────┐
│ 🔍 Scanning Status: 🟢 Active                        │
│ 📊 Scan Count: 1247                                  │
│ 🏷️  AirTags Found: 2                                 │
│ ⏰ Device Timeout: 60s                               │
│ 🔄 Scan Interval: 1.0s                              │
└──────────────────────────────────────────────────────┘

┌─────────────────── 🏷️  Detected AirTags ──────────────────┐
│ Address            │  RSSI │ Distance │ Trend │ Count │ Last Seen │
├────────────────────┼───────┼──────────┼───────┼───────┼───────────┤
│ AA:BB:CC:DD:EE:FF  │ -45dBm│     2.1m │   ↗   │    23 │ 2s ago    │
│ 11:22:33:44:55:66  │ -67dBm│     8.5m │   →   │    15 │ 1s ago    │
└────────────────────┴───────┴──────────┴───────┴───────┴───────────┘
```

### WSS - WiFi skenování
```
┌─────────────────── WiFi Scan #42 - 14:30:15 ───────────────────┐
│ SSID              │ Security    │ Signal │ Band   │ BSSID         │ Quality   │
├───────────────────┼─────────────┼────────┼────────┼───────────────┼───────────┤
│ OpenWiFi          │ 🔓 OPEN     │   85%  │ 2.4GHz │ AA:BB:CC:...  │ Excellent │
│ MyNetwork         │ 🔒 WPA2     │   72%  │ 5GHz   │ 11:22:33:...  │ Good      │
└───────────────────┴─────────────┴────────┴────────┴───────────────┴───────────┘
```

## 🛠️ Řešení problémů

### Chybějící závislosti
```bash
# Python závislosti
pip install -r requirements.txt

# Systémové závislosti (Ubuntu/Debian)
sudo apt install bluetooth bluez network-manager wireless-tools

# Fedora/RHEL
sudo dnf install bluez NetworkManager wireless-tools
```

### Problémy s oprávněními
```bash
# Pro BLE přístup (PyTAG)
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)

# Nebo spusťte jako root
sudo python3 main.py

# Přidání uživatele do bluetooth skupiny
sudo usermod -a -G bluetooth $USER
# (vyžaduje odhlášení a přihlášení)
```

### Bluetooth problémy
```bash
# Zkontrolujte stav Bluetooth
sudo systemctl status bluetooth

# Restartujte Bluetooth službu
sudo systemctl restart bluetooth

# Povolte Bluetooth
sudo systemctl enable bluetooth
```

### WiFi problémy
```bash
# Zkontrolujte NetworkManager
sudo systemctl status NetworkManager

# Restartujte NetworkManager
sudo systemctl restart NetworkManager

# Zkontrolujte WiFi rozhraní
ip link show
```

## 📁 Struktura projektu

```
WBS/
├── wbs.py                 # 🚀 Hlavní aplikace (spouštěcí soubor)
├── requirements.txt        # Python závislosti
├── README.md              # Tato dokumentace
├── install.sh             # Instalační skript
├── run.sh                 # Spouštěcí skript (doporučeno)
├── clean.sh               # Čistící skript
├── .gitignore             # Git ignore soubory
├── modules/               # Moduly aplikace
│   ├── __init__.py
│   ├── pytag_module.py    # PyTAG funkcionalita
│   └── wss_module.py      # WSS funkcionalita
├── config/                # Konfigurace
│   └── app_config.json    # Nastavení aplikace
└── wifi_logs/             # WiFi logy (generované)
```

## 🧹 Čištění projektu

Pro vyčištění dočasných souborů a cache:

```bash
# Interaktivní režim
./clean.sh

# Vyčistit vše
./clean.sh --all

# Vyčistit pouze Python cache
./clean.sh --cache

# Odstranit virtuální prostředí
./clean.sh --venv

# Vyčistit logy
./clean.sh --logs
```

## 🔒 Bezpečnostní poznámky

- **Root oprávnění**: Některé funkce vyžadují root přístup pro BLE a síťové operace
- **Síťové připojení**: WSS auto-connect může měnit síťová připojení
- **Bluetooth**: PyTAG skenuje BLE zařízení v okolí
- **Soukromí**: Nástroje detekují pouze veřejně dostupné informace

## 📝 Licence

Tento projekt je licencován pod MIT licencí - stejně jako původní PyTAG a WSS projekty.

## 🙏 Poděkování

- **Původní PyTAG**: Portováno z ESP32 AirTagTag projektu
- **WSS**: WiFi Scanner Suite
- **Knihovny**: bleak (BLE), rich (UI)

## 🔗 Související projekty

- [PyTAG](../PyTAG/) - Samostatný PyTAG projekt
- [WSS](../wss/) - Samostatný WSS projekt
- [ESP32 AirTagTag](https://github.com/7ENSOR/AirTagTag) - Původní ESP32 verze

---

**Vytvořeno s ❤️ pro open source komunitu**

**Author: OK2HSS | Version: 1.0.0**
