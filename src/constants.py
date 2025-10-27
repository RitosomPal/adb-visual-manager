"""Application constants and configuration"""

# Application Info
APP_NAME = "ADB Visual Manager"
APP_VERSION = "1.0.0"
ORGANIZATION = "YourOrganization"
APP_ICON_PATH = "resources/icons/icon.ico"

# ADB Configuration
DEFAULT_ADB_HOST = "127.0.0.1"
DEFAULT_ADB_PORT = 5037
DEFAULT_DEVICE_PORT = 5555

# Connection Types
CONNECTION_USB = "USB"
CONNECTION_NETWORK = "Network"

# UI Configuration - Dynamic sizing (will be calculated at runtime)
DEFAULT_THEME = "dark"

# Window startup mode
WINDOW_START_MAXIMIZED = True  # ADD THIS LINE - Set to False for normal size

# Absolute minimum sizes (safe for any screen)
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 500

# Preferred window size as percentage of screen (will be calculated)
WINDOW_WIDTH_PERCENT = 0.60  # 70% of screen width
WINDOW_HEIGHT_PERCENT = 0.65  # 75% of screen height

# Maximum window size as percentage of screen
WINDOW_MAX_WIDTH_PERCENT = 0.90
WINDOW_MAX_HEIGHT_PERCENT = 0.85

# Refresh Intervals (milliseconds)
PROCESS_MONITOR_REFRESH = 2000
DEVICE_REFRESH_INTERVAL = 5000
LOGCAT_BUFFER_SIZE = 10000

# Timeouts (seconds)
ADB_CONNECT_TIMEOUT = 10
FILE_TRANSFER_TIMEOUT = 300

# File Transfer
DEFAULT_TRANSFER_CHUNK_SIZE = 1024 * 1024  # 1MB
