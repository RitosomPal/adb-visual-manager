"""File system data model"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileItem:
    """Represents a file or directory"""
    name: str
    path: str
    size: int = 0  # Size in bytes
    modified_date: Optional[datetime] = None
    permissions: str = "----------"
    is_directory: bool = False
    is_symlink: bool = False
    owner: str = "root"
    
    @property
    def size_mb(self):
        """Get size in MB"""
        return round(self.size / (1024 * 1024), 2)
    
    @property
    def size_kb(self):
        """Get size in KB"""
        return round(self.size / 1024, 2)
    
    @property
    def size_formatted(self):
        """Get human-readable size"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size_kb} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size_mb} MB"
        else:
            gb = round(self.size / (1024 * 1024 * 1024), 2)
            return f"{gb} GB"
    
    @property
    def file_type(self):
        """Get file type"""
        if self.is_directory:
            return "Folder"
        elif self.is_symlink:
            return "Link"
        else:
            # Get extension
            if '.' in self.name:
                ext = self.name.split('.')[-1].upper()
                return f"{ext} File"
            return "File"
    
    def __str__(self):
        return self.name
