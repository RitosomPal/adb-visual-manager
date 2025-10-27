"""Device data models and structures"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DeviceInfo:
    """Represents Android device information"""
    serial: str
    model: str = "Unknown"
    android_version: str = "Unknown"
    sdk_version: str = "Unknown"
    battery_level: int = 0
    connection_type: str = "Unknown"  # USB or Network
    screen_resolution: str = "Unknown"
    is_connected: bool = True
    ip_address: Optional[str] = None
    manufacturer: str = "Unknown"
    
    def __str__(self):
        return f"{self.model} ({self.serial})"
    
    @property
    def display_name(self):
        """User-friendly display name"""
        if self.model != "Unknown":
            return f"{self.manufacturer} {self.model}"
        return self.serial
