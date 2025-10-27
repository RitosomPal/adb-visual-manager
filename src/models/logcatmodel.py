"""Logcat data model"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    pid: int
    tid: int
    level: str  # V, D, I, W, E, F
    tag: str
    message: str
    
    @property
    def level_text(self):
        """Get full level name"""
        levels = {
            'V': 'Verbose',
            'D': 'Debug',
            'I': 'Info',
            'W': 'Warning',
            'E': 'Error',
            'F': 'Fatal',
        }
        return levels.get(self.level, 'Unknown')
    
    @property
    def level_color(self):
        """Get color for this log level"""
        colors = {
            'V': '#888888',  # Gray
            'D': '#4ec9b0',  # Cyan
            'I': '#ffffff',  # White
            'W': '#dcdcaa',  # Yellow
            'E': '#f48771',  # Red
            'F': '#d16969',  # Dark Red
        }
        return colors.get(self.level, '#ffffff')
    
    def __str__(self):
        return f"{self.timestamp} {self.level}/{self.tag}: {self.message}"
