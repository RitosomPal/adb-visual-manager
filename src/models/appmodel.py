"""Application data models"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class AppInfo:
    """Represents an Android application"""
    package_name: str
    app_name: str = "Unknown"
    version: str = "Unknown"
    version_code: str = "Unknown"
    install_date: Optional[datetime] = None
    size: int = 0  # Size in bytes
    is_system: bool = False
    is_running: bool = False
    is_enabled: bool = True
    
    @property
    def size_mb(self):
        """Get size in MB"""
        return round(self.size / (1024 * 1024), 2)
    
    @property
    def app_type(self):
        """Get app type string"""
        return "System" if self.is_system else "User"
    
    @property
    def status(self):
        """Get app status string - FIXED"""
        if self.is_running:
            return "Running"
        else:
            return "Not Running"
    
    def __str__(self):
        return f"{self.app_name} ({self.package_name})"

