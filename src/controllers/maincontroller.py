"""Main application controller"""

import logging
from PyQt5.QtCore import QTimer

from models.adbmanager import ADBManager
from views.mainwindow import MainWindow
from controllers.terminalcontroller import TerminalController
from controllers.appcontroller import AppController
from controllers.filecontroller import FileController
from controllers.processcontroller import ProcessController
from controllers.logcatcontroller import LogcatController
from controllers.remotecontroller import RemoteController
from constants import DEVICE_REFRESH_INTERVAL

logger = logging.getLogger(__name__)


class MainController:
    """Central application coordinator"""
    
    def __init__(self, adb_manager: ADBManager):
        """
        Initialize main controller
        
        Args:
            adb_manager: ADB manager instance
        """
        self.adb_manager = adb_manager
        self.main_window = MainWindow()
        self.current_device_serial = None
        
        # Initialize terminal controller
        self.terminal_controller = TerminalController(
            self.main_window.terminal_widget,
            self.adb_manager
        )
        
        # Initialize app controller
        self.app_controller = AppController(
            self.main_window.app_manager_widget,
            self.adb_manager,
            self.main_window
        )

        # Initialize file controller
        self.file_controller = FileController(
            self.main_window.file_explorer_widget,
            self.adb_manager,
            self.main_window
        )

        # Initialize process controller (NEW)
        self.process_controller = ProcessController(
            self.main_window.process_monitor_widget,
            self.adb_manager,
            self.main_window
        )
        
        # Initialize logcat controller (NEW)
        self.logcat_controller = LogcatController(
            self.main_window.logcat_widget,
            self.adb_manager,
            self.main_window
        )

        # Initialize remote control controller
        self.remote_controller = RemoteController(
            self.main_window.remote_control_widget,
            self.adb_manager,
            self.main_window
        )
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_devices)
        
        self.setup_connections()
        logger.info("Main controller initialized")
    
    def setup_connections(self):
        """Connect signals and slots"""
        # Device panel signals
        self.main_window.device_panel.connect_requested.connect(
            self.handle_connect_request
        )
        self.main_window.device_panel.disconnect_requested.connect(
            self.handle_disconnect_request
        )
        self.main_window.device_panel.device_selected.connect(
            self.handle_device_selected
        )
        self.main_window.device_panel.refresh_requested.connect(
            self.refresh_devices
        )
    
    def initialize(self):
        """Initialize application state"""
        logger.info("Initializing application")
        
        # Check ADB status
        if self.adb_manager.is_adb_running():
            self.main_window.set_adb_status(True)
            self.main_window.set_status_message("ADB server connected")
            
            # Load initial devices
            self.refresh_devices()
            
            # Optional: Start auto-refresh (can be toggled later)
            # Uncomment the next line if you want auto-refresh
            # self.refresh_timer.start(DEVICE_REFRESH_INTERVAL)
            
        else:
            self.main_window.set_adb_status(False)
            self.main_window.show_error(
                "ADB Error",
                "ADB server is not running!\n\n"
                "Please ensure:\n"
                "1. ADB is installed\n"
                "2. ADB is in your system PATH\n"
                "3. Run 'adb start-server' in terminal"
            )
        
        # Show main window
        self.main_window.show()
    
    def toggle_auto_refresh(self, enabled):
        """
        Toggle auto-refresh on/off
        
        Args:
            enabled: True to enable auto-refresh
        """
        if enabled:
            self.refresh_timer.start(DEVICE_REFRESH_INTERVAL)
            logger.info("Auto-refresh enabled")
        else:
            self.refresh_timer.stop()
            logger.info("Auto-refresh disabled")

    def handle_connect_request(self, ip, port):
        """
        Handle device connection request
        
        Args:
            ip: Device IP address
            port: Device port
        """
        logger.info(f"Attempting to connect to {ip}:{port}")
        self.main_window.set_status_message(f"Connecting to {ip}:{port}...")
        
        success = self.adb_manager.connect_device(ip, port)
        
        if success:
            self.main_window.set_status_message(f"Connected to {ip}:{port}")
            self.main_window.show_info("Success", f"Connected to {ip}:{port}")
            self.refresh_devices()
        else:
            self.main_window.set_status_message("Connection failed")
            self.main_window.show_error(
                "Connection Failed",
                f"Could not connect to {ip}:{port}\n\n"
                "Please ensure:\n"
                "1. Device is on the same network\n"
                "2. ADB over network is enabled on device\n"
                "3. IP address and port are correct"
            )
    
    def handle_disconnect_request(self, serial):
        """
        Handle device disconnection request
        
        Args:
            serial: Device serial number
        """
        logger.info(f"Disconnecting device: {serial}")
        
        if self.main_window.confirm_action(
            "Disconnect Device",
            f"Are you sure you want to disconnect {serial}?"
        ):
            success = self.adb_manager.disconnect_device(serial)
            
            if success:
                self.main_window.set_status_message(f"Disconnected from {serial}")
                self.refresh_devices()
            else:
                self.main_window.show_error(
                    "Disconnect Failed",
                    f"Could not disconnect {serial}"
                )
    
    def handle_device_selected(self, serial):
        """
        Handle device selection change
        
        Args:
            serial: Selected device serial
        """
        logger.info(f"Device selected: {serial}")
        self.current_device_serial = serial
        self.main_window.set_status_message(f"Selected device: {serial}")
        
        # Update dashboard with device info
        self.update_device_dashboard(serial)

        # Update terminal with selected device
        self.terminal_controller.set_device(serial)

        # Update app manager with selected device
        self.app_controller.set_device(serial)

        # Update file explorer
        self.file_controller.set_device(serial)

        # Update process monitor
        self.process_controller.set_device(serial)

        # Update logcat viewer
        self.logcat_controller.set_device(serial)

        # Update remote control (NEW)
        self.remote_controller.set_device(serial)
    
    def update_device_dashboard(self, serial):
        """
        Update dashboard with device information
        
        Args:
            serial: Device serial number
        """
        # Get basic device info from cached devices
        devices = self.adb_manager.get_devices()
        device_info = next((d for d in devices if d.serial == serial), None)
        
        if device_info:
            self.main_window.dashboard_widget.update_device_info(device_info)
            
            # Get extended info in background (to avoid UI blocking)
            extended_info = self.adb_manager.get_extended_device_info(serial)
            self.main_window.dashboard_widget.update_extended_info(extended_info)
            
            logger.info(f"Updated dashboard for {serial}")
        else:
            self.main_window.dashboard_widget.show_no_device()

    def refresh_devices(self):
        """Refresh device list"""
        logger.info("Refreshing device list")
        devices = self.adb_manager.get_devices()
        self.main_window.device_panel.update_devices(devices)
        
        # If a device is currently selected, update its dashboard
        if self.current_device_serial:
            device_still_connected = any(d.serial == self.current_device_serial for d in devices)
            if device_still_connected:
                self.update_device_dashboard(self.current_device_serial)
            else:
                # Device disconnected
                self.current_device_serial = None
                self.main_window.dashboard_widget.show_no_device()
        
        logger.info(f"Found {len(devices)} device(s)")
    
    def auto_refresh_devices(self):
        """Auto-refresh device list (called by timer)"""
        if self.adb_manager.is_adb_running():
            self.refresh_devices()
        else:
            self.main_window.set_adb_status(False)
            self.refresh_timer.stop()
    
    def shutdown(self):
        """Cleanup on application exit"""
        logger.info("Shutting down application")
        self.refresh_timer.stop()
        
        # TODO: Stop all monitoring threads
        # TODO: Save settings
