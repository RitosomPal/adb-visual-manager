# 📱 ADB Visual Manager

A comprehensive desktop application for managing Android devices via ADB protocol with a modern, user-friendly interface.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ Features

### 🔌 Device Management

- Multi-device support (USB & Network)
- Automatic device discovery
- Connect devices by IP address
- Real-time device status

### 📊 Dashboard

- Device information display
- Model, Android version, serial number
- Battery status and IP address
- Quick device overview

### 💻 Terminal

- Interactive ADB shell
- Command history
- Common commands shortcuts
- Copy output on double-click

### 📦 Application Manager

- List user and system apps
- Install/Uninstall APKs
- Start/Stop applications
- Force stop running apps
- Real-time running status (🟢/🔴)
- Search and filter apps

### 📁 File Explorer

- Dual-pane file browser (Device & Local)
- Upload/Download files
- Directory navigation with symlink support
- Create folders, Delete, Rename
- Show hidden files
- Quick access bookmarks
- Context menus

### 🔍 Process Monitor

- List all running processes
- View memory usage
- Kill/Force kill processes
- Search and filter
- Auto-refresh (5 seconds)
- Sort by any column

### 📋 Logcat Viewer

- Real-time log streaming
- Filter by log level (V, D, I, W, E, F)
- Tag filtering
- Search functionality
- Auto-scroll
- Export logs to file
- Pause/Resume streaming

### 🎮 Remote Control

- Live screen preview
- Touch screen interaction (tap & swipe)
- Text input
- Hardware buttons (Home, Back, Menu, Power)
- Volume controls
- D-Pad navigation (Android TV)
- Screenshot capture
- Auto-refresh screen

## 📋 Requirements

### System Requirements

- Windows 10/11, Linux (Ubuntu 20.04+), or macOS 11+
- Python 3.8 or higher
- ADB (Android Debug Bridge) installed and in PATH

### Python Dependencies

```text
PyQt5>=5.15.0
pure-python-adb>=0.3.0
```

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/adb-visual-manager.git
cd adb-visual-manager
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install ADB

- **Windows**: Download from [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
- **Linux**: `sudo apt-get install android-tools-adb`
- **macOS**: `brew install android-platform-tools`

### 4. Verify ADB Installation

```bash
adb version
```

## 📖 Usage

### Starting the Application

```bash
python src/main.py
```

### Connect a Device

#### USB Connection

1. Enable USB debugging on your Android device
2. Connect via USB cable
3. Accept the debugging prompt on your device
4. Device will appear in the dropdown

#### Network Connection

1. Enable USB debugging and Network debugging
2. Connect device via USB first
3. Find device IP: Settings → About → Status → IP address
4. Click "📱 Connect IP" button
5. Enter device IP and port (default: 5555)
6. Device will appear in the dropdown

### Using Features

#### Dashboard

- View device information and status
- Check battery level and connectivity

#### Terminal

- Type ADB shell commands
- Use common commands from the shortcuts
- Double-click to copy output

#### Applications

- Select "User Apps" or "System Apps"
- Install APK by clicking "📥 Install APK"
- Uninstall by selecting app and clicking "🗑️ Uninstall"
- Start/Stop apps with respective buttons

#### File Explorer

- Navigate device files on the left
- Navigate local files on the right
- Drag & drop or use Upload/Download buttons
- Right-click for context menu

#### Processes

- View all running processes
- Search by name, PID, or user
- Right-click to kill process
- Enable auto-refresh for live updates

#### Logcat

- Click "▶ Start" to begin streaming
- Select log level filter
- Use tag filter for specific components
- Click "💾 Export" to save logs

#### Remote Control

- Click/tap on screen preview to interact
- Use hardware buttons for navigation
- Type text to send to device
- Enable auto-refresh for live screen updates

## 🛠️ Configuration

### Log Files

Application logs are stored in:

- Windows: `%APPDATA%/ADBVisualManager/logs/`
- Linux/macOS: `~/.config/ADBVisualManager/logs/`

### Settings

Settings file location:

- Windows: `%APPDATA%/ADBVisualManager/config.json`
- Linux/macOS: `~/.config/ADBVisualManager/config.json`

## 🎨 Customization

### Themes

Edit `resources/styles/dark_theme.qss` to customize colors and styling.

## 🐛 Troubleshooting

### Device Not Detected

- Ensure USB debugging is enabled
- Check USB cable connection
- Run `adb devices` in terminal to verify
- Try a different USB port

### Permission Denied Errors

- Some operations require root access
- User apps can be managed without root
- System apps require root permissions

### Connection Issues

- Verify device IP address
- Ensure device and computer are on same network
- Check firewall settings
- Default ADB port is 5555

### Screenshot/Screen Preview Not Working

- Requires Android 5.0+ for screenshots
- Check storage permissions
- Some devices may restrict screen capture

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 👨‍💻 Author

- [@RitosomPal](https://github.com/RitosomPal)

## 🙏 Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Uses [pure-python-adb](https://github.com/Swind/pure-python-adb)
- Inspired by Android development tools

## 📞 Support

- Report bugs: [GitHub Issues](https://github.com/yourusername/adb-visual-manager/issues)
- Documentation: [Wiki](https://github.com/yourusername/adb-visual-manager/wiki)

## 🗺️ Roadmap

- [ ] Screen recording
- [ ] Batch operations
- [ ] APK backup/restore
- [ ] Wireless debugging (Android 11+)
- [ ] Plugin system
- [ ] Multi-language support

---

**Made with ❤️ for Android developers and enthusiasts**
