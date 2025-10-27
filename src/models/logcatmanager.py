"""Logcat management model"""

import logging
import re
import subprocess
from typing import Optional, Callable
from models.logcatmodel import LogEntry

logger = logging.getLogger(__name__)


class LogcatManager:
    """Handle logcat streaming and management"""
    
    def __init__(self, adb_manager):
        """Initialize logcat manager"""
        self.adb_manager = adb_manager
        self._stop_streaming = False
        logger.info("Logcat manager initialized")
    
    def clear_logcat(self, device_serial: str) -> bool:
        """
        Clear logcat buffer
        
        Args:
            device_serial: Device serial number
            
        Returns:
            True if successful
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info("Clearing logcat buffer")
            device.shell("logcat -c")
            logger.info("Logcat cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing logcat: {e}")
            return False
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a logcat line
        
        Format: 01-27 13:30:45.123  1234  5678 I Tag: Message
        
        Args:
            line: Single line from logcat
            
        Returns:
            LogEntry or None
        """
        try:
            # Regex pattern for logcat format
            # Format: MM-DD HH:MM:SS.mmm  PID  TID LEVEL TAG: Message
            pattern = r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+(.+?):\s+(.+)'
            
            match = re.match(pattern, line)
            if match:
                timestamp, pid, tid, level, tag, message = match.groups()
                
                return LogEntry(
                    timestamp=timestamp,
                    pid=int(pid),
                    tid=int(tid),
                    level=level,
                    tag=tag.strip(),
                    message=message.strip()
                )
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing log line: {e}")
            return None
    
    def start_logcat_stream(self, device_serial: str, callback: Callable[[str], None], 
                           level_filter: str = 'V', tag_filter: str = None):
        """
        Start streaming logcat using subprocess (FIXED)
        
        Args:
            device_serial: Device serial number
            callback: Function to call for each log line
            level_filter: Minimum log level (V, D, I, W, E, F)
            tag_filter: Optional tag filter
        """
        try:
            # Build adb command
            cmd = ["adb", "-s", device_serial, "logcat", "-v", "time"]
            
            # Add level filter
            if level_filter and level_filter != 'V':
                cmd.append(f"*:{level_filter}")
            
            # Add tag filter
            if tag_filter:
                cmd.extend([f"{tag_filter}:*", "*:S"])
            
            logger.info(f"Starting logcat stream: {' '.join(cmd)}")
            
            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Read lines
            self._stop_streaming = False
            while not self._stop_streaming:
                line = process.stdout.readline()
                if not line:
                    break
                
                callback(line.rstrip('\n'))
            
            # Cleanup
            process.terminate()
            process.wait()
            
        except Exception as e:
            logger.error(f"Logcat stream error: {e}")
            raise
    
    def stop_streaming(self):
        """Signal to stop streaming"""
        self._stop_streaming = True
