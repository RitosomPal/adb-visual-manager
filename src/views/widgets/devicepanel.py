"""Device connection and selection panel"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QComboBox, 
    QPushButton, QLabel, QLineEdit, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon

class ConnectDialog(QDialog):
    """Dialog for entering IP address to connect"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Device")
        self.setModal(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # IP Address input
        ip_label = QLabel("Device IP Address:")
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        
        # Port input
        port_label = QLabel("Port:")
        self.port_input = QLineEdit()
        self.port_input.setText("5555")
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(ip_label)
        layout.addWidget(self.ip_input)
        layout.addWidget(port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_connection_info(self):
        """Get IP and port from dialog"""
        ip = self.ip_input.text().strip()
        port = int(self.port_input.text()) if self.port_input.text().isdigit() else 5555
        return ip, port


class DevicePanel(QWidget):
    """Device selection and connection management panel"""
    
    # Signals
    connect_requested = pyqtSignal(str, int)  # ip, port
    disconnect_requested = pyqtSignal(str)  # serial
    device_selected = pyqtSignal(str)  # serial
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_devices = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup device panel UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Device selector
        device_label = QLabel("Device:")
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.device_combo.currentTextChanged.connect(self.on_device_selected)
        
        # Status indicator
        self.status_label = QLabel("No devices")
        self.status_label.setStyleSheet("color: #888;")
        
        # Buttons
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        
        # Layout
        layout.addWidget(device_label)
        layout.addWidget(self.device_combo)
        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)
        layout.addWidget(self.refresh_btn)
        
        self.setLayout(layout)
    
    def on_connect_clicked(self):
        """Handle connect button click"""
        dialog = ConnectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            ip, port = dialog.get_connection_info()
            if ip:
                self.connect_requested.emit(ip, port)
    
    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        current_serial = self.device_combo.currentData()
        if current_serial:
            self.disconnect_requested.emit(current_serial)
    
    def on_refresh_clicked(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
    
    def on_device_selected(self, text):
        """Handle device selection change"""
        serial = self.device_combo.currentData()
        if serial:
            self.device_selected.emit(serial)
            # Enable disconnect only for network devices
            is_network = ":" in serial
            self.disconnect_btn.setEnabled(is_network)
    
    def update_devices(self, devices):
        """
        Update device list
        
        Args:
            devices: List of DeviceInfo objects
        """
        self.current_devices = devices
        current_serial = self.device_combo.currentData()
        
        # Clear and repopulate
        self.device_combo.clear()
        
        if not devices:
            self.status_label.setText("No devices connected")
            self.status_label.setStyleSheet("color: #888;")
            self.disconnect_btn.setEnabled(False)
            return
        
        # Add devices to combo box
        for device in devices:
            display_text = f"{device.display_name} ({device.serial})"
            self.device_combo.addItem(display_text, device.serial)
        
        # Restore previous selection if still available
        if current_serial:
            index = self.device_combo.findData(current_serial)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
        
        # Update status
        count = len(devices)
        self.status_label.setText(f"{count} device(s) connected")
        self.status_label.setStyleSheet("color: #4CAF50;")
    
    def get_selected_device_serial(self):
        """Get currently selected device serial"""
        return self.device_combo.currentData()
