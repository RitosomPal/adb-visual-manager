"""Terminal controller for ADB shell command execution"""

import logging
from PyQt5.QtCore import QObject

logger = logging.getLogger(__name__)


class TerminalController(QObject):
    """Controller for terminal widget and ADB shell execution"""
    
    def __init__(self, terminal_widget, adb_manager):
        """
        Initialize terminal controller
        
        Args:
            terminal_widget: TerminalWidget instance
            adb_manager: ADBManager instance
        """
        super().__init__()
        self.terminal_widget = terminal_widget
        self.adb_manager = adb_manager
        self.current_device_serial = None
        self._last_connected_serial = None
        
        self.setup_connections()
        logger.info("Terminal controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.terminal_widget.command_entered.connect(self.execute_command)
    
    def set_device(self, serial):
        """
        Set current device for terminal
        
        Args:
            serial: Device serial number
        """
        # Only show message if device actually changed
        if serial == self._last_connected_serial:  # ADD THIS CHECK
            return  # Device hasn't changed, don't show message again
        
        self.current_device_serial = serial
        self._last_connected_serial = serial  # UPDATE TRACKING
        
        if serial:
            self.terminal_widget.set_device_connected(True)
            device = self.adb_manager.get_device_by_serial(serial)
            if device:
                self.terminal_widget.append_output(
                    f"\n✓ Connected to device: {serial}\n",
                    "#00ffff"
                )
        else:
            self.terminal_widget.set_device_connected(False)
            self.current_device_serial = None
            self._last_connected_serial = None  # RESET TRACKING
    
    def execute_command(self, command):
        """
        Execute ADB shell command
        
        Args:
            command: Shell command to execute
        """
        if not self.current_device_serial:
            self.terminal_widget.display_error("No device selected")
            return
        
        device = self.adb_manager.get_device_by_serial(self.current_device_serial)
        if not device:
            self.terminal_widget.display_error("Device not found or disconnected")
            return
        
        try:
            logger.info(f"Executing command: {command}")
            
            # Execute shell command
            output = device.shell(command)
            
            # Display output
            if output:
                self.terminal_widget.display_output(output)
            else:
                self.terminal_widget.display_output("(no output)\n")
            
            logger.info(f"Command executed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Command execution failed: {error_msg}")
            self.terminal_widget.display_error(error_msg)
