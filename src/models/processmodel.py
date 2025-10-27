"""Process data model"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessInfo:
    """Represents a running process"""
    pid: int
    name: str
    user: str = "unknown"
    cpu_percent: float = 0.0
    mem_percent: float = 0.0
    mem_size: int = 0  # Memory in KB
    state: str = "R"  # Running, Sleeping, etc.
    ppid: int = 0  # Parent process ID
    
    @property
    def mem_mb(self):
        """Get memory in MB"""
        return round(self.mem_size / 1024, 2)
    
    @property
    def state_text(self):
        """Get human-readable state"""
        states = {
            'R': 'Running',
            'S': 'Sleeping',
            'D': 'Disk Sleep',
            'Z': 'Zombie',
            'T': 'Stopped',
            'W': 'Paging',
        }
        return states.get(self.state, 'Unknown')
    
    def __str__(self):
        return f"{self.name} (PID: {self.pid})"
