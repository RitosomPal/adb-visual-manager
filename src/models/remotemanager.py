"""Remote control manager"""

import logging
from typing import Tuple
from models.remotecontrol import KeyCode

logger = logging.getLogger(__name__)


class RemoteManager:
    """Handle remote control operations"""
    
    def __init__(self, adb_manager):
        """Initialize remote manager"""
        self.adb_manager = adb_manager
        logger.info("Remote manager initialized")
    
    def send_tap(self, device_serial: str, x: int, y: int) -> bool:
        """
        Send tap event
        
        Args:
            device_serial: Device serial number
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Tap at ({x}, {y})")
            device.shell(f"input tap {x} {y}")
            return True
        except Exception as e:
            logger.error(f"Tap failed: {e}")
            return False
    
    def send_swipe(self, device_serial: str, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """
        Send swipe gesture
        
        Args:
            device_serial: Device serial number
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Swipe duration in ms
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Swipe from ({x1}, {y1}) to ({x2}, {y2})")
            device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")
            return True
        except Exception as e:
            logger.error(f"Swipe failed: {e}")
            return False
    
    def send_text(self, device_serial: str, text: str) -> bool:
        """
        Send text input
        
        Args:
            device_serial: Device serial number
            text: Text to send
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            # Escape special characters
            escaped_text = text.replace(' ', '%s').replace('&', '\\&')
            logger.info(f"Sending text: {text}")
            device.shell(f"input text '{escaped_text}'")
            return True
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            return False
    
    def send_keyevent(self, device_serial: str, keycode: KeyCode) -> bool:
        """
        Send key event
        
        Args:
            device_serial: Device serial number
            keycode: KeyCode enum
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Key event: {keycode.name}")
            device.shell(f"input keyevent {keycode.value}")
            return True
        except Exception as e:
            logger.error(f"Key event failed: {e}")
            return False
    
    def get_screen_size(self, device_serial: str) -> Tuple[int, int]:
        """
        Get device screen size
        
        Args:
            device_serial: Device serial number
            
        Returns:
            Tuple of (width, height)
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return (1080, 1920)  # Default
        
        try:
            output = device.shell("wm size")
            # Parse: Physical size: 1080x1920
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split('x'))
                logger.info(f"Screen size: {width}x{height}")
                return (width, height)
        except Exception as e:
            logger.error(f"Failed to get screen size: {e}")
        
        return (1080, 1920)  # Default fallback
    
    def take_screenshot(self, device_serial: str, local_path: str) -> bool:
        """
        Take screenshot and save to local path
        
        Args:
            device_serial: Device serial number
            local_path: Local file path to save
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Taking screenshot -> {local_path}")
            
            # Take screenshot on device
            device.shell("screencap -p /sdcard/screenshot.png")
            
            # Pull to local
            device.pull("/sdcard/screenshot.png", local_path)
            
            # Clean up
            device.shell("rm /sdcard/screenshot.png")
            
            logger.info("Screenshot saved")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False
