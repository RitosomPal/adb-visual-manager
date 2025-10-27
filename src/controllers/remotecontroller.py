"""Remote control controller"""

import tempfile
import os
import logging
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from models.remotemanager import RemoteManager
from models.remotecontrol import KeyCode

logger = logging.getLogger(__name__)


class RemoteController(QObject):
    """Remote control controller"""
    
    def __init__(self, remote_widget, adb_manager, main_window=None):
        super().__init__()
        self.remote_widget = remote_widget
        self.adb_manager = adb_manager
        self.remote_manager = RemoteManager(adb_manager)
        self.main_window = main_window
        self.current_device_serial = None
        self._last_connected_serial = None
        self.temp_screenshot_path = None
        
        self.setup_connections()
        logger.info("Remote controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.remote_widget.tap_requested.connect(self.send_tap)
        self.remote_widget.swipe_requested.connect(self.send_swipe)
        self.remote_widget.text_requested.connect(self.send_text)
        self.remote_widget.key_requested.connect(self.send_key)
        self.remote_widget.screenshot_requested.connect(self.take_screenshot)
        self.remote_widget.auto_refresh_requested.connect(
            lambda: self.refresh_screen_preview(force=False)
        )
        self.remote_widget.manual_refresh_requested.connect(
            lambda: self.refresh_screen_preview(force=True)
        )
    
    def set_device(self, serial):
        """Set current device"""
        if serial == self._last_connected_serial:
            return
        
        self.current_device_serial = serial
        self._last_connected_serial = serial
        
        if serial:
            self.remote_widget.set_device_connected(True)
            # Get and set screen size
            width, height = self.remote_manager.get_screen_size(serial)
            self.remote_widget.set_screen_size(width, height)
        else:
            self.remote_widget.set_device_connected(False)
            self._last_connected_serial = None

    def refresh_screen_preview(self, force=False):
        """
        Refresh screen preview with new screenshot
        
        Args:
            force: If True, refresh even if auto-refresh is disabled
        """
        if not self.current_device_serial:
            return
        
        # Check if auto-refresh is enabled (unless forced)
        if not force and not self.remote_widget.auto_refresh_enabled:
            logger.info("Auto-refresh disabled, skipping")
            return
        
        try:
            # Create temp file for screenshot
            if not self.temp_screenshot_path:
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()
                self.temp_screenshot_path = os.path.join(temp_dir, "adb_screen_preview.png")
            
            logger.info("Refreshing screen preview...")
            
            # Take screenshot
            success = self.remote_manager.take_screenshot(
                self.current_device_serial,
                self.temp_screenshot_path
            )
            
            if success:
                # Update preview
                self.remote_widget.update_screen_preview(self.temp_screenshot_path)
                logger.info("Screen preview updated")
            else:
                logger.warning("Failed to refresh screen preview")
                
        except Exception as e:
            logger.error(f"Error refreshing screen: {e}")

    def send_tap(self, x, y):
        """Send tap event to device"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Sending tap: ({x}, {y})")
        
        success = self.remote_manager.send_tap(self.current_device_serial, x, y)
        
        if not success:
            logger.warning("Tap failed")
    
    def send_swipe(self, x1, y1, x2, y2):
        """Send swipe gesture to device"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Sending swipe: ({x1}, {y1}) -> ({x2}, {y2})")
        
        success = self.remote_manager.send_swipe(
            self.current_device_serial, x1, y1, x2, y2
        )
        
        if not success:
            logger.warning("Swipe failed")
    
    def send_text(self, text):
        """Send text input to device"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Sending text: {text}")
        
        success = self.remote_manager.send_text(self.current_device_serial, text)
        
        if success:
            if self.main_window:
                self.main_window.set_status_message(f"Sent text: {text}")
        else:
            QMessageBox.warning(
                self.remote_widget,
                "Failed",
                "Failed to send text"
            )
    
    def send_key(self, key_name):
        """Send key event to device"""
        if not self.current_device_serial:
            return
        
        try:
            # Convert string to KeyCode enum
            keycode = KeyCode[key_name]
            logger.info(f"Sending key: {key_name}")
            
            success = self.remote_manager.send_keyevent(
                self.current_device_serial, keycode
            )
            
            if success:
                if self.main_window:
                    self.main_window.set_status_message(f"Key: {key_name}")

                # Auto-refresh screen after button press (if enabled)
                if self.remote_widget.auto_refresh_enabled:
                    from PyQt5.QtCore import QTimer
                    # Delay refresh to allow screen to update
                    QTimer.singleShot(500, lambda: self.refresh_screen_preview(force=False))
            else:
                logger.warning(f"Key {key_name} failed")
                
        except KeyError:
            logger.error(f"Unknown key: {key_name}")
    
    def take_screenshot(self, file_path):
        """Take screenshot and save"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Taking screenshot -> {file_path}")
        
        if self.main_window:
            self.main_window.set_status_message("Taking screenshot...")
        
        success = self.remote_manager.take_screenshot(
            self.current_device_serial, file_path
        )
        
        if success:
            QMessageBox.information(
                self.remote_widget,
                "Success",
                f"Screenshot saved to:\n{file_path}"
            )
            if self.main_window:
                self.main_window.set_status_message("Screenshot saved")
        else:
            QMessageBox.critical(
                self.remote_widget,
                "Failed",
                "Screenshot failed"
            )
            if self.main_window:
                self.main_window.set_status_message("Screenshot failed")
