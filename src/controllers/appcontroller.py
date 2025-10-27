"""Application manager controller - Production Ready"""

import logging
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox, QProgressDialog

from models.appmanager import AppManager

logger = logging.getLogger(__name__)


class AppLoadWorker(QThread):
    """Background worker for loading apps"""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # current, total
    
    def __init__(self, app_manager, device_serial, show_system):
        super().__init__()
        self.app_manager = app_manager
        self.device_serial = device_serial
        self.show_system = show_system
    
    def run(self):
        """Load apps in background"""
        try:
            apps = self.app_manager.list_installed_apps(
                self.device_serial,
                self.show_system
            )
            self.finished.emit(apps)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.error.emit(str(e))


class AppController(QObject):
    """Application manager controller"""
    
    def __init__(self, app_widget, adb_manager, main_window=None):
        super().__init__()
        self.app_widget = app_widget
        self.adb_manager = adb_manager
        self.app_manager = AppManager(adb_manager)
        self.main_window = main_window
        self.current_device_serial = None
        self._last_connected_serial = None
        self.load_worker = None
        
        self.setup_connections()
        logger.info("App controller initialized")
    
    def setup_connections(self):
        """Setup signal connections"""
        self.app_widget.refresh_requested.connect(self.load_apps)
        self.app_widget.install_requested.connect(self.install_apk)
        self.app_widget.uninstall_requested.connect(self.uninstall_app)
        self.app_widget.start_requested.connect(self.start_app)
        self.app_widget.stop_requested.connect(self.stop_app)
        self.app_widget.clear_data_requested.connect(self.clear_app_data)
    
    def set_device(self, serial):
        """Set current device"""
        if serial == self._last_connected_serial:
            return
        
        self.current_device_serial = serial
        self._last_connected_serial = serial
        
        if serial:
            self.app_widget.set_device_connected(True)
            self.load_apps(show_system=False)
        else:
            self.app_widget.set_device_connected(False)
            self._last_connected_serial = None
    
    def load_apps(self, show_system=False):
        """Load apps from device"""
        if not self.current_device_serial:
            logger.warning("No device selected")
            return
        
        # Cancel existing worker
        if self.load_worker and self.load_worker.isRunning():
            self.load_worker.terminate()
            self.load_worker.wait()
        
        logger.info(f"Loading apps (system={show_system})")
        
        # Show progress
        self.progress = QProgressDialog(
            "Loading applications...",
            None,
            0,
            0,
            self.app_widget
        )
        self.progress.setWindowTitle("Please Wait")
        self.progress.setModal(True)
        self.progress.show()
        
        # Start worker
        self.load_worker = AppLoadWorker(
            self.app_manager,
            self.current_device_serial,
            show_system
        )
        self.load_worker.finished.connect(self.on_apps_loaded)
        self.load_worker.error.connect(self.on_load_error)
        self.load_worker.start()
    
    def on_apps_loaded(self, apps):
        """Handle apps loaded"""
        self.progress.close()
        self.app_widget.update_apps(apps)
        logger.info(f"Loaded {len(apps)} apps")
        
        if self.main_window:
            self.main_window.set_status_message(f"Loaded {len(apps)} applications")
    
    def on_load_error(self, error):
        """Handle load error"""
        self.progress.close()
        QMessageBox.critical(
            self.app_widget,
            "Error",
            f"Failed to load apps:\n{error}"
        )
    
    def install_apk(self, apk_path):
        """Install APK"""
        if not self.current_device_serial:
            return
        
        logger.info(f"Installing: {apk_path}")
        
        progress = QMessageBox(self.app_widget)
        progress.setWindowTitle("Installing")
        progress.setText("Installing APK...\nPlease wait.")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.show()
        
        success = self.app_manager.install_apk(self.current_device_serial, apk_path)
        progress.close()
        
        if success:
            QMessageBox.information(self.app_widget, "Success", "App installed successfully!")
            self.load_apps(self.app_widget.show_system_check.isChecked())
        else:
            QMessageBox.critical(self.app_widget, "Failed", "Installation failed")
    
    def uninstall_app(self, package_name):
        """Uninstall app"""
        if not self.current_device_serial:
            return
        
        success = self.app_manager.uninstall_app(self.current_device_serial, package_name)
        
        if success:
            QMessageBox.information(self.app_widget, "Success", f"Uninstalled {package_name}")
            self.load_apps(self.app_widget.show_system_check.isChecked())
        else:
            QMessageBox.critical(self.app_widget, "Failed", f"Uninstall failed")
    
    def start_app(self, package_name):
        """Start app"""
        if not self.current_device_serial:
            return
        
        success = self.app_manager.start_app(self.current_device_serial, package_name)
        
        if success:
            if self.main_window:
                self.main_window.set_status_message(f"Started {package_name}")
            # Refresh status after 1 second
            QTimer.singleShot(1000, lambda: self.refresh_single_app(package_name))
        else:
            QMessageBox.warning(
                self.app_widget,
                "Failed",
                f"Could not start {package_name}\n\nApp may not have a launcher activity."
            )
    
    def stop_app(self, package_name):
        """Stop app"""
        if not self.current_device_serial:
            return
        
        success = self.app_manager.stop_app(self.current_device_serial, package_name)
        
        if success:
            if self.main_window:
                self.main_window.set_status_message(f"Stopped {package_name}")
            # Refresh status immediately
            QTimer.singleShot(500, lambda: self.refresh_single_app(package_name))
        else:
            QMessageBox.critical(self.app_widget, "Failed", "Stop failed")
    
    def clear_app_data(self, package_name):
        """Clear app data"""
        if not self.current_device_serial:
            return
        
        reply = QMessageBox.question(
            self.app_widget,
            "Confirm",
            f"Clear all data for {package_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        success = self.app_manager.clear_app_data(self.current_device_serial, package_name)
        
        if success:
            QMessageBox.information(self.app_widget, "Success", "Data cleared")
        else:
            QMessageBox.critical(self.app_widget, "Failed", "Clear failed")
    
    def refresh_single_app(self, package_name):
        """Refresh single app status (fast update)"""
        for i, app in enumerate(self.app_widget.filtered_apps):
            if app.package_name == package_name:
                # Get updated running status
                is_running = self.app_manager.is_app_running(
                    self.current_device_serial,
                    package_name
                )
                
                # Get updated info
                updated_app = self.app_manager.get_app_info(
                    self.current_device_serial,
                    package_name,
                    is_running,
                    app.is_system
                )
                
                if updated_app:
                    # Update lists
                    self.app_widget.filtered_apps[i] = updated_app
                    
                    for j, main_app in enumerate(self.app_widget.apps):
                        if main_app.package_name == package_name:
                            self.app_widget.apps[j] = updated_app
                            break
                    
                    # Refresh display
                    self.app_widget.populate_table()
                    logger.info(f"Refreshed {package_name}: Running={updated_app.is_running}")
                break
