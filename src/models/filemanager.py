"""File system operations manager - Symlink Resolution with Path Preservation"""

import logging
from typing import List, Optional, Tuple
import os

from models.filemodel import FileItem

logger = logging.getLogger(__name__)


class FileManager:
    """Handle device file system operations"""
    
    def __init__(self, adb_manager):
        """Initialize file manager"""
        self.adb_manager = adb_manager
        self._symlink_map = {}  # Maps display paths to real paths
        logger.info("File manager initialized")
    
    def list_directory(self, device_serial: str, display_path: str, show_hidden: bool = False) -> List[FileItem]:
        """
        List directory contents - resolves symlinks but preserves display paths
        
        Args:
            device_serial: Device serial number
            display_path: Path to display (may contain symlinks like /sdcard)
            show_hidden: Whether to show hidden files (starting with .)
            
        Returns:
            List of FileItem objects with display paths
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            logger.error(f"Device {device_serial} not found")
            return []
        
        try:
            # Normalize path
            display_path = display_path.replace('\\', '/')
            logger.info(f"Listing directory: {display_path} (hidden={show_hidden})")
            
            # Resolve the actual path (for listing)
            actual_path = self._resolve_symlink(device, display_path)
            logger.info(f"Resolved: {display_path} -> {actual_path}")
            
            # Use ls -la if showing hidden files, ls -l otherwise
            if show_hidden:
                cmd = f"ls -la '{actual_path}' 2>&1"
            else:
                cmd = f"ls -l '{actual_path}' 2>&1"
            
            output = device.shell(cmd).strip()
            
            # Check for errors
            if "Permission denied" in output:
                logger.warning(f"Permission denied: {actual_path}")
                return []
            
            if "No such file" in output or not output:
                logger.warning(f"Path not found: {actual_path}")
                return []
            
            files = []
            lines = output.split('\n')
            
            # Parse each line with display path prefix
            for line in lines:
                if not line.strip() or line.startswith('total'):
                    continue
                
                # Parse and build display paths
                file_item = self._parse_ls_line(line, display_path, actual_path, device)
                
                # Filter out . and .. entries
                if file_item and file_item.name not in ['.', '..']:
                    # If not showing hidden, skip files starting with .
                    if not show_hidden and file_item.name.startswith('.'):
                        continue
                    
                    files.append(file_item)
            
            # Sort: directories first, then files
            files.sort(key=lambda x: (not x.is_directory, x.name.lower()))
            
            logger.info(f"Listed {len(files)} items")
            return files
            
        except Exception as e:
            logger.error(f"Error listing directory {display_path}: {e}", exc_info=True)
            return []

    def _resolve_symlink(self, device, path: str) -> str:
        """
        Resolve symlink to actual path (recursive)
        
        Args:
            device: ADB device instance
            path: Path that may be a symlink
            
        Returns:
            Resolved actual path
        """
        original_path = path
        visited = set()
        max_depth = 10
        
        for _ in range(max_depth):
            if path in visited:
                logger.warning(f"Circular symlink: {path}")
                break
            
            visited.add(path)
            
            # Check if this is a symlink
            ls_output = device.shell(f"ls -ld '{path}' 2>/dev/null").strip()
            
            if '->' in ls_output:
                # It's a symlink, extract target
                parts = ls_output.split('->')
                if len(parts) == 2:
                    target = parts[1].strip()
                    
                    # Make absolute if relative
                    if not target.startswith('/'):
                        parent = os.path.dirname(path)
                        target = os.path.join(parent, target).replace('\\', '/')
                    
                    logger.debug(f"Symlink: {path} -> {target}")
                    path = target
                    continue
            
            # Not a symlink, we're done
            break
        
        # Store mapping for reverse lookup
        if path != original_path:
            self._symlink_map[original_path] = path
        
        return path
    
    def _parse_ls_line(self, line: str, display_base: str, actual_base: str, device) -> Optional[FileItem]:
        """
        Parse ls -l output with display path preservation
        
        Args:
            line: Single line from ls -l
            display_base: Display path (may contain symlinks like /sdcard)
            actual_base: Actual resolved path
            device: ADB device instance
            
        Returns:
            FileItem with display path
        """
        try:
            parts = line.split()
            if len(parts) < 8:
                return None
            
            permissions = parts[0]
            owner = parts[2]
            size = int(parts[4]) if parts[4].isdigit() else 0
            name = ' '.join(parts[7:])
            
            # Handle symlinks in name
            if '->' in name:
                name = name.split('->')[0].strip()
            
            # Determine type
            is_symlink = permissions.startswith('l')
            is_directory = permissions.startswith('d')
            
            # Build DISPLAY path (preserve symlink prefix)
            if display_base.endswith('/'):
                display_path = f"{display_base}{name}"
            else:
                display_path = f"{display_base}/{name}"
            
            # If this item is a symlink, check if it points to directory
            if is_symlink:
                # Build actual path for testing
                if actual_base.endswith('/'):
                    actual_item_path = f"{actual_base}{name}"
                else:
                    actual_item_path = f"{actual_base}/{name}"
                
                # Test if directory
                test_result = device.shell(f"test -d '{actual_item_path}' && echo '1' || echo '0'").strip()
                if test_result == '1':
                    is_directory = True
            
            return FileItem(
                name=name,
                path=display_path,  # This preserves /sdcard/Pictures, etc.
                size=size,
                permissions=permissions,
                is_directory=is_directory,
                is_symlink=is_symlink,
                owner=owner
            )
            
        except Exception as e:
            logger.debug(f"Error parsing line: {e}")
            return None
    
    def push_file(self, device_serial: str, local_path: str, remote_path: str) -> bool:
        """Upload file (handles symlink paths)"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            # Normalize
            remote_path = remote_path.replace('\\', '/')
            
            logger.info(f"Uploading {local_path} -> {remote_path}")
            
            # Push directly - ppadb handles symlinks
            device.push(local_path, remote_path)
            logger.info("Upload successful")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            
            # Fallback to /sdcard/Download
            try:
                filename = os.path.basename(local_path)
                fallback = f"/sdcard/Download/{filename}"
                logger.info(f"Retrying: {fallback}")
                device.push(local_path, fallback)
                logger.info("Upload successful (fallback)")
                return True
            except Exception as e2:
                logger.error(f"Fallback failed: {e2}")
                return False
    
    def pull_file(self, device_serial: str, remote_path: str, local_path: str) -> bool:
        """Download file (handles symlink paths)"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            remote_path = remote_path.replace('\\', '/')
            
            logger.info(f"Downloading {remote_path} -> {local_path}")
            device.pull(remote_path, local_path)
            logger.info("Download successful")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def delete_file(self, device_serial: str, path: str, is_directory: bool = False) -> bool:
        """Delete file or directory"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            path = path.replace('\\', '/')
            
            cmd = f"rm -r '{path}'" if is_directory else f"rm '{path}'"
            
            logger.info(f"Deleting: {path}")
            result = device.shell(cmd)
            
            success = "No such file" not in result and "Permission denied" not in result
            if success:
                logger.info("Delete successful")
            return success
            
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def create_directory(self, device_serial: str, path: str) -> bool:
        """Create directory"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            path = path.replace('\\', '/')
            
            logger.info(f"Creating directory: {path}")
            result = device.shell(f"mkdir -p '{path}'")
            
            success = "Permission denied" not in result
            return success
            
        except Exception as e:
            logger.error(f"Create directory failed: {e}")
            return False
    
    def rename_file(self, device_serial: str, old_path: str, new_path: str) -> bool:
        """Rename/move file or directory"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            old_path = old_path.replace('\\', '/')
            new_path = new_path.replace('\\', '/')
            
            logger.info(f"Renaming {old_path} -> {new_path}")
            result = device.shell(f"mv '{old_path}' '{new_path}'")
            
            success = "No such file" not in result and "Permission denied" not in result
            return success
            
        except Exception as e:
            logger.error(f"Rename failed: {e}")
            return False
