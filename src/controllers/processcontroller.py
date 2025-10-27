"""Process monitor controller"""

import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from models.processmanager import ProcessManager

logger = logging.getLogger(__name__)


class ProcessLoadWorker(QThread):
    """Background worker for loading processes"""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, process_manager, device_serial):
        super().__init__()
        self.process_manager = process_manager
        self.device_serial = device_serial
    
    def run(self):
        """Load processes in background"""
        try:
            processes = self.process_manager.list_processes(self.device_serial)
            self.finished.emit(processes)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.error.emit(str(e))


class ProcessController(QObject):
    """Process monitor controller"""
    
    def __init__(self, process_widget, adb_manager, main_window=None):
        super().__init__()
        self.process_widget = process_widget
        self.adb_manager = adb_manager
        self.process_manager = ProcessManager(adb_manager)
        self.main_window = main_window
        self.current_device_serial = None
        self._last_connected_serial = None
        self.load_worker = None
        
        self.setup_connections()
        logger.info("Process controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.process_widget.refresh_requested.connect(self.load_processes)
        self.process_widget.kill_requested.connect(self.kill_process)
        self.process_widget.force_kill_requested.connect(self.force_kill_process)
    
    def set_device(self, serial):
        """Set current device"""
        if serial == self._last_connected_serial:
            return
        
        self.current_device_serial = serial
        self._last_connected_serial = serial
        
        if serial:
            self.process_widget.set_device_connected(True)
            # Auto-load processes when device is selected
            self.load_processes()
        else:
            self.process_widget.set_device_connected(False)
            self._last_connected_serial = None
    
    def load_processes(self):
        """Load processes from device"""
        if not self.current_device_serial:
            logger.warning("No device selected")
            return
        
        # Cancel existing worker
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()
            self.load_worker.wait()
        
        logger.info("Loading processes...")
        
        # Start worker
        self.load_worker = ProcessLoadWorker(
            self.process_manager,
            self.current_device_serial
        )
        self.load_worker.finished.connect(self.on_processes_loaded)
        self.load_worker.error.connect(self.on_load_error)
        self.load_worker.start()
    
    def on_processes_loaded(self, processes):
        """Handle processes loaded"""
        self.process_widget.update_processes(processes)
        logger.info(f"Loaded {len(processes)} processes")
        
        if self.main_window:
            self.main_window.set_status_message(f"Loaded {len(processes)} processes")
    
    def on_load_error(self, error):
        """Handle load error"""
        QMessageBox.critical(
            self.process_widget,
            "Error",
            f"Failed to load processes:\n{error}"
        )
    
    def kill_process(self, pid):
        """Kill process by PID"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Killing process PID {pid}")
        
        success = self.process_manager.kill_process(self.current_device_serial, pid)
        
        if success:
            QMessageBox.information(
                self.process_widget,
                "Success",
                f"Process {pid} killed successfully"
            )
            # Reload process list
            self.load_processes()
        else:
            # Show detailed error message
            QMessageBox.critical(
                self.process_widget,
                "Kill Failed",
                f"Failed to kill process {pid}\n\n"
                f"Possible reasons:\n"
                f"• Process already terminated\n"
                f"• System process (requires root)\n"
                f"• Insufficient permissions\n\n"
                f"Try using 'Force Kill' from right-click menu for app processes."
            )
    
    def force_kill_process(self, pid):
        """Force kill process by PID"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Force killing process PID {pid}")
        
        success = self.process_manager.force_kill_process(self.current_device_serial, pid)
        
        if success:
            QMessageBox.information(
                self.process_widget,
                "Success",
                f"Process {pid} force killed (SIGKILL)"
            )
            # Reload process list
            self.load_processes()
        else:
            QMessageBox.critical(
                self.process_widget,
                "Force Kill Failed",
                f"Failed to force kill process {pid}\n\n"
                f"This process cannot be killed:\n"
                f"• System/protected process\n"
                f"• Requires root access\n"
                f"• Process already terminated\n\n"
                f"Only user apps and non-system processes can be killed."
            )
