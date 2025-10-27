"""File explorer controller - Production Ready"""

import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
import os

from models.filemanager import FileManager

logger = logging.getLogger(__name__)


class FileLoadWorker(QThread):
    """Background worker for loading files"""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, file_manager, device_serial, path, show_hidden=False):
        super().__init__()
        self.file_manager = file_manager
        self.device_serial = device_serial
        self.path = path
        self.show_hidden = show_hidden
    
    def run(self):
        """Load files in background"""
        try:
            files = self.file_manager.list_directory(
                self.device_serial, 
                self.path,
                self.show_hidden
            )
            self.finished.emit(files)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.error.emit(str(e))



class FileController(QObject):
    """File explorer controller"""
    
    def __init__(self, file_widget, adb_manager, main_window=None):
        super().__init__()
        self.file_widget = file_widget
        self.adb_manager = adb_manager
        self.file_manager = FileManager(adb_manager)
        self.main_window = main_window
        self.current_device_serial = None
        self._last_connected_serial = None
        self.load_worker = None
        self.show_hidden = False
        
        self.setup_connections()
        logger.info("File controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.file_widget.path_changed.connect(self.load_device_files)
        self.file_widget.upload_requested.connect(self.upload_file)
        self.file_widget.download_requested.connect(self.download_file)
        self.file_widget.delete_requested.connect(self.delete_file)
        self.file_widget.rename_requested.connect(self.rename_file)
        self.file_widget.create_folder_requested.connect(self.create_folder)
        self.file_widget.show_hidden_changed.connect(self.on_show_hidden_changed)

    def on_show_hidden_changed(self, show_hidden):
        """Handle show hidden files toggle"""
        self.show_hidden = show_hidden
        logger.info(f"Show hidden files changed: {show_hidden}")
    
    def set_device(self, serial):
        """Set current device"""
        if serial == self._last_connected_serial:
            return
        
        self.current_device_serial = serial
        self._last_connected_serial = serial
        
        if serial:
            self.file_widget.set_device_connected(True)
            # Load /sdcard (display path)
            self.load_device_files("/sdcard")
            self.file_widget.refresh_local_files()
        else:
            self.file_widget.set_device_connected(False)
            self._last_connected_serial = None
    
    def load_device_files(self, path):
        """Load device files"""
        if not self.current_device_serial:
            logger.warning("No device selected")
            return
        
        # Cancel existing worker
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()
            self.load_worker.wait()
        
        logger.info(f"Loading files from {path} (hidden={self.show_hidden})")
        
        # Start worker with show_hidden flag
        self.load_worker = FileLoadWorker(
            self.file_manager,
            self.current_device_serial,
            path,
            self.show_hidden  # ADD THIS PARAMETER
        )
        self.load_worker.finished.connect(self.on_files_loaded)
        self.load_worker.error.connect(self.on_load_error)
        self.load_worker.start()
    
    def on_files_loaded(self, files):
        """Handle files loaded"""
        self.file_widget.update_device_files(files)
        logger.info(f"Loaded {len(files)} files")
    
    def on_load_error(self, error):
        """Handle load error"""
        QMessageBox.critical(
            self.file_widget,
            "Error",
            f"Failed to load files:\n{error}"
        )
    
    def upload_file(self, local_path, remote_path):
        """Upload file to device"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Uploading {local_path} -> {remote_path}")
        
        if self.main_window:
            self.main_window.set_status_message(f"Uploading {os.path.basename(local_path)}...")
        
        success = self.file_manager.push_file(
            self.current_device_serial,
            local_path,
            remote_path
        )
        
        if success:
            QMessageBox.information(
                self.file_widget,
                "Success",
                f"Uploaded successfully to:\n{remote_path}"
            )
            # Refresh current directory
            current_path = self.file_widget.current_device_path
            self.load_device_files(current_path)
            
            if self.main_window:
                self.main_window.set_status_message("Upload complete")
        else:
            QMessageBox.critical(
                self.file_widget,
                "Failed",
                f"Upload failed.\n\nTarget: {remote_path}\n\nCheck logs for details."
            )
            if self.main_window:
                self.main_window.set_status_message("Upload failed")
    
    def download_file(self, remote_path, local_path):
        """Download file from device"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Downloading {remote_path} -> {local_path}")
        
        if self.main_window:
            self.main_window.set_status_message(f"Downloading...")
        
        success = self.file_manager.pull_file(
            self.current_device_serial,
            remote_path,
            local_path
        )
        
        if success:
            QMessageBox.information(
                self.file_widget,
                "Success",
                f"Downloaded to:\n{local_path}"
            )
            self.file_widget.refresh_local_files()
            
            if self.main_window:
                self.main_window.set_status_message("Download complete")
        else:
            QMessageBox.critical(
                self.file_widget,
                "Failed",
                "Download failed"
            )
            if self.main_window:
                self.main_window.set_status_message("Download failed")
    
    def delete_file(self, path, is_directory):
        """Delete file from device"""
        if not self.current_device_serial:
            return
        
        success = self.file_manager.delete_file(
            self.current_device_serial,
            path,
            is_directory
        )
        
        if success:
            QMessageBox.information(
                self.file_widget,
                "Success",
                "Deleted successfully"
            )
            # Refresh
            current_path = self.file_widget.current_device_path
            self.load_device_files(current_path)
        else:
            QMessageBox.critical(
                self.file_widget,
                "Failed",
                "Delete failed (check permissions)"
            )
    
    def rename_file(self, old_path, new_path):
        """Rename file on device"""
        if not self.current_device_serial:
            return
        
        success = self.file_manager.rename_file(
            self.current_device_serial,
            old_path,
            new_path
        )
        
        if success:
            QMessageBox.information(
                self.file_widget,
                "Success",
                "Renamed successfully"
            )
            # Refresh
            current_path = self.file_widget.current_device_path
            self.load_device_files(current_path)
        else:
            QMessageBox.critical(
                self.file_widget,
                "Failed",
                "Rename failed"
            )
    
    def create_folder(self, path):
        """Create folder on device"""
        if not self.current_device_serial:
            return
        
        success = self.file_manager.create_directory(
            self.current_device_serial,
            path
        )
        
        if success:
            QMessageBox.information(
                self.file_widget,
                "Success",
                "Folder created"
            )
            # Refresh
            current_path = self.file_widget.current_device_path
            self.load_device_files(current_path)
        else:
            QMessageBox.critical(
                self.file_widget,
                "Failed",
                "Create folder failed (check permissions)"
            )
