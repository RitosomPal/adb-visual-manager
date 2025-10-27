"""Process management model"""

import logging
from typing import List, Optional
import re

from models.processmodel import ProcessInfo

logger = logging.getLogger(__name__)


class ProcessManager:
    """Handle process monitoring and management"""
    
    def __init__(self, adb_manager):
        """Initialize process manager"""
        self.adb_manager = adb_manager
        logger.info("Process manager initialized")
    
    def list_processes(self, device_serial: str) -> List[ProcessInfo]:
        """
        List all running processes
        
        Args:
            device_serial: Device serial number
            
        Returns:
            List of ProcessInfo objects
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            logger.error(f"Device {device_serial} not found")
            return []
        
        try:
            logger.info("Listing processes...")
            
            # Get process list using ps
            # Format: PID USER VSZ STAT COMMAND
            output = device.shell("ps -A -o PID,USER,VSZ,STAT,NAME").strip()
            
            if not output:
                logger.warning("No process output")
                return []
            
            processes = []
            lines = output.split('\n')
            
            # Skip header line
            for line in lines[1:]:
                if not line.strip():
                    continue
                
                process = self._parse_ps_line(line)
                if process:
                    processes.append(process)
            
            logger.info(f"Found {len(processes)} processes")
            return processes
            
        except Exception as e:
            logger.error(f"Error listing processes: {e}", exc_info=True)
            return []
    
    def _parse_ps_line(self, line: str) -> Optional[ProcessInfo]:
        """
        Parse ps output line
        
        Format: PID USER VSZ STAT NAME
        Example: 1234 u0_a123 1234567 S com.android.systemui
        
        Args:
            line: Single line from ps output
            
        Returns:
            ProcessInfo or None
        """
        try:
            parts = line.split()
            if len(parts) < 5:
                return None
            
            pid = int(parts[0])
            user = parts[1]
            vsz = int(parts[2]) if parts[2].isdigit() else 0  # Memory in KB
            state = parts[3][0] if parts[3] else 'R'  # First char is state
            name = ' '.join(parts[4:])
            
            return ProcessInfo(
                pid=pid,
                name=name,
                user=user,
                mem_size=vsz,
                state=state
            )
            
        except Exception as e:
            logger.debug(f"Error parsing line '{line}': {e}")
            return None
    
    def kill_process(self, device_serial: str, pid: int) -> bool:
        """
        Kill a process by PID
        
        Args:
            device_serial: Device serial number
            pid: Process ID to kill
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Killing process PID {pid}")
            
            # Try normal kill first
            result = device.shell(f"kill {pid} 2>&1")
            
            # Check if successful
            if "No such process" in result:
                logger.warning(f"Process {pid} not found")
                return False
            
            if "Permission denied" in result or "Operation not permitted" in result:
                # Try with run-as or su if available
                logger.info("Permission denied, trying alternative methods...")
                
                # Try killing through am (for apps)
                try:
                    # Get process info to find package name
                    ps_result = device.shell(f"ps -p {pid} -o NAME").strip()
                    lines = ps_result.split('\n')
                    if len(lines) > 1:
                        package_name = lines[1].strip()
                        if '.' in package_name:  # Looks like a package name
                            logger.info(f"Trying to force-stop app: {package_name}")
                            device.shell(f"am force-stop {package_name}")
                            return True
                except:
                    pass
                
                logger.warning(f"Insufficient permissions to kill process {pid}")
                return False
            
            logger.info(f"Process {pid} killed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error killing process: {e}")
            return False
    
    def force_kill_process(self, device_serial: str, pid: int) -> bool:
        """
        Force kill a process (SIGKILL)
        
        Args:
            device_serial: Device serial number
            pid: Process ID to kill
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Force killing process PID {pid}")
            
            # Try kill -9 first
            result = device.shell(f"kill -9 {pid} 2>&1")
            
            # Check result
            if "No such process" in result:
                logger.warning(f"Process {pid} not found")
                return False
            
            if "Permission denied" in result or "Operation not permitted" in result:
                # Try alternative method through am
                logger.info("Permission denied, trying app force-stop...")
                
                try:
                    # Get package name from PID
                    ps_result = device.shell(f"ps -p {pid} -o NAME").strip()
                    lines = ps_result.split('\n')
                    if len(lines) > 1:
                        package_name = lines[1].strip()
                        if '.' in package_name:
                            logger.info(f"Force-stopping app: {package_name}")
                            device.shell(f"am force-stop {package_name}")
                            
                            # Also try kill command
                            device.shell(f"am kill {package_name}")
                            return True
                except Exception as e:
                    logger.error(f"Alternative kill failed: {e}")
                
                logger.warning(f"Insufficient permissions to kill process {pid}")
                return False
            
            logger.info(f"Process {pid} force killed")
            return True
            
        except Exception as e:
            logger.error(f"Error force killing process: {e}")
            return False

    def get_process_info(self, device_serial: str, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed info about a specific process
        
        Args:
            device_serial: Device serial number
            pid: Process ID
            
        Returns:
            ProcessInfo or None
        """
        processes = self.list_processes(device_serial)
        
        for process in processes:
            if process.pid == pid:
                return process
        
        return None
