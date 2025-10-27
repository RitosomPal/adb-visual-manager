"""Logcat viewer controller"""

import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

from models.logcatmanager import LogcatManager

logger = logging.getLogger(__name__)


class LogcatStreamWorker(QThread):
    """Background worker for logcat streaming"""
    
    log_received = pyqtSignal(str)  # Raw log line
    error = pyqtSignal(str)
    
    def __init__(self, logcat_manager, device_serial, level_filter, tag_filter):
        super().__init__()
        self.logcat_manager = logcat_manager
        self.device_serial = device_serial
        self.level_filter = level_filter
        self.tag_filter = tag_filter
    
    def run(self):
        """Stream logcat in background"""
        try:
            def callback(line):
                self.log_received.emit(line)
            
            self.logcat_manager.start_logcat_stream(
                self.device_serial,
                callback,
                self.level_filter,
                self.tag_filter
            )
        except Exception as e:
            logger.error(f"Logcat stream error: {e}", exc_info=True)
            self.error.emit(str(e))
    
    def stop(self):
        """Stop streaming"""
        self.logcat_manager.stop_streaming()


class LogcatController(QObject):
    """Logcat viewer controller"""
    
    def __init__(self, logcat_widget, adb_manager, main_window=None):
        super().__init__()
        self.logcat_widget = logcat_widget
        self.adb_manager = adb_manager
        self.logcat_manager = LogcatManager(adb_manager)
        self.main_window = main_window
        self.current_device_serial = None
        self._last_connected_serial = None
        self.stream_worker = None
        
        self.setup_connections()
        logger.info("Logcat controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.logcat_widget.clear_requested.connect(self.clear_logcat)
        self.logcat_widget.start_requested.connect(self.start_streaming)
        self.logcat_widget.stop_requested.connect(self.stop_streaming)
        self.logcat_widget.export_requested.connect(self.export_logs)
    
    def set_device(self, serial):
        """Set current device"""
        if serial == self._last_connected_serial:
            return
        
        # Stop any existing stream
        if self.stream_worker:
            self.stop_streaming()
        
        self.current_device_serial = serial
        self._last_connected_serial = serial
        
        if serial:
            self.logcat_widget.set_device_connected(True)
        else:
            self.logcat_widget.set_device_connected(False)
            self._last_connected_serial = None
    
    def clear_logcat(self):
        """Clear logcat buffer on device"""
        if not self.current_device_serial:
            return
        
        success = self.logcat_manager.clear_logcat(self.current_device_serial)
        
        if success:
            logger.info("Logcat buffer cleared")
            if self.main_window:
                self.main_window.set_status_message("Logcat cleared")
        else:
            QMessageBox.warning(
                self.logcat_widget,
                "Warning",
                "Failed to clear logcat buffer"
            )
    
    def start_streaming(self, level_filter, tag_filter):
        """Start logcat streaming"""
        if not self.current_device_serial:
            return
        
        # Stop existing stream
        if self.stream_worker and self.stream_worker.isRunning():
            self.stop_streaming()
        
        logger.info(f"Starting logcat stream (level={level_filter}, tag={tag_filter})")
        
        # Create and start worker
        self.stream_worker = LogcatStreamWorker(
            self.logcat_manager,
            self.current_device_serial,
            level_filter,
            tag_filter
        )
        self.stream_worker.log_received.connect(self.on_log_received)
        self.stream_worker.error.connect(self.on_stream_error)
        self.stream_worker.start()
        
        if self.main_window:
            self.main_window.set_status_message("Logcat streaming started")
    
    def stop_streaming(self):
        """Stop logcat streaming"""
        if self.stream_worker:
            logger.info("Stopping logcat stream")
            
            # Signal worker to stop
            self.stream_worker.stop()
            
            # Wait for graceful shutdown
            if not self.stream_worker.wait(2000):
                # Force terminate if needed
                self.stream_worker.terminate()
                self.stream_worker.wait()
            
            self.stream_worker = None
        
        if self.main_window:
            self.main_window.set_status_message("Logcat streaming stopped")

    
    def on_log_received(self, line):
        """Handle received log line"""
        if not line.strip():
            return
        
        # Try to parse the line
        log_entry = self.logcat_manager.parse_log_line(line)
        
        if log_entry:
            # Successfully parsed - add formatted log
            self.logcat_widget.append_log(log_entry)
        else:
            # Couldn't parse - show raw line anyway
            self.logcat_widget.append_log(line)

    
    def on_stream_error(self, error):
        """Handle stream error"""
        logger.error(f"Logcat stream error: {error}")
        QMessageBox.critical(
            self.logcat_widget,
            "Stream Error",
            f"Logcat stream error:\n{error}"
        )
        self.stop_streaming()
    
    def export_logs(self, file_path):
        """Export logs to file"""
        try:
            content = self.logcat_widget.log_display.toPlainText()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(
                self.logcat_widget,
                "Success",
                f"Logs exported to:\n{file_path}"
            )
            
            logger.info(f"Logs exported to {file_path}")
            
            if self.main_window:
                self.main_window.set_status_message("Logs exported successfully")
        
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self.logcat_widget,
                "Export Failed",
                f"Failed to export logs:\n{e}"
            )
