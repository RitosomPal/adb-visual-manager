"""Device information display widget"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class InfoLabel(QWidget):
    """Custom widget for displaying label-value pairs"""
    
    def __init__(self, label, value="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.label = QLabel(f"{label}:")
        self.label.setStyleSheet("color: #888; font-weight: bold;")
        self.label.setMinimumWidth(120)
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: #bbbbbb;")
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        layout.addWidget(self.label)
        layout.addWidget(self.value_label, 1)
        self.setLayout(layout)
    
    def set_value(self, value):
        """Update the value"""
        self.value_label.setText(str(value))


class DeviceInfoWidget(QWidget):
    """Comprehensive device information display"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device_info = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup device info UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("Device Information")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Device Details Group
        self.create_device_details_group()
        layout.addWidget(self.device_details_group)
        
        # System Info Group
        self.create_system_info_group()
        layout.addWidget(self.system_info_group)
        
        # Hardware Info Group
        self.create_hardware_info_group()
        layout.addWidget(self.hardware_info_group)
        
        # Battery Info Group
        self.create_battery_info_group()
        layout.addWidget(self.battery_info_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Show no device message initially
        self.show_no_device()
    
    def create_device_details_group(self):
        """Create device details group"""
        self.device_details_group = QGroupBox("Device Details")
        layout = QVBoxLayout()
        
        self.model_info = InfoLabel("Model")
        self.manufacturer_info = InfoLabel("Manufacturer")
        self.serial_info = InfoLabel("Serial Number")
        self.connection_info = InfoLabel("Connection Type")
        self.ip_info = InfoLabel("IP Address")
        
        layout.addWidget(self.model_info)
        layout.addWidget(self.manufacturer_info)
        layout.addWidget(self.serial_info)
        layout.addWidget(self.connection_info)
        layout.addWidget(self.ip_info)
        
        self.device_details_group.setLayout(layout)
    
    def create_system_info_group(self):
        """Create system info group"""
        self.system_info_group = QGroupBox("System Information")
        layout = QVBoxLayout()
        
        self.android_version_info = InfoLabel("Android Version")
        self.sdk_version_info = InfoLabel("SDK Version")
        self.build_info = InfoLabel("Build Number")
        self.security_patch_info = InfoLabel("Security Patch")
        
        layout.addWidget(self.android_version_info)
        layout.addWidget(self.sdk_version_info)
        layout.addWidget(self.build_info)
        layout.addWidget(self.security_patch_info)
        
        self.system_info_group.setLayout(layout)
    
    def create_hardware_info_group(self):
        """Create hardware info group"""
        self.hardware_info_group = QGroupBox("Hardware Information")
        layout = QVBoxLayout()
        
        self.screen_resolution_info = InfoLabel("Screen Resolution")
        self.cpu_info = InfoLabel("CPU")
        self.ram_info = InfoLabel("RAM")
        self.storage_info = InfoLabel("Storage")
        
        layout.addWidget(self.screen_resolution_info)
        layout.addWidget(self.cpu_info)
        layout.addWidget(self.ram_info)
        layout.addWidget(self.storage_info)
        
        self.hardware_info_group.setLayout(layout)
    
    def create_battery_info_group(self):
        """Create battery info group"""
        self.battery_info_group = QGroupBox("Battery Status")
        layout = QVBoxLayout()
        
        # Battery level with progress bar
        battery_layout = QVBoxLayout()
        battery_label_layout = QHBoxLayout()
        
        self.battery_label = QLabel("Battery Level:")
        self.battery_label.setStyleSheet("color: #888; font-weight: bold;")
        self.battery_value = QLabel("0%")
        self.battery_value.setStyleSheet("color: #bbbbbb;")
        
        battery_label_layout.addWidget(self.battery_label)
        battery_label_layout.addWidget(self.battery_value)
        battery_label_layout.addStretch()
        
        self.battery_progress = QProgressBar()
        self.battery_progress.setMinimum(0)
        self.battery_progress.setMaximum(100)
        self.battery_progress.setValue(0)
        self.battery_progress.setTextVisible(False)
        self.battery_progress.setFixedHeight(20)
        
        battery_layout.addLayout(battery_label_layout)
        battery_layout.addWidget(self.battery_progress)
        
        # Battery details
        self.battery_status_info = InfoLabel("Status")
        self.battery_health_info = InfoLabel("Health")
        self.battery_temp_info = InfoLabel("Temperature")
        
        layout.addLayout(battery_layout)
        layout.addWidget(self.battery_status_info)
        layout.addWidget(self.battery_health_info)
        layout.addWidget(self.battery_temp_info)
        
        self.battery_info_group.setLayout(layout)
    
    def update_device_info(self, device_info):
        """
        Update displayed device information
        
        Args:
            device_info: DeviceInfo object
        """
        if device_info is None:
            self.show_no_device()
            return
        
        self.current_device_info = device_info
        
        # Device Details
        self.model_info.set_value(device_info.model)
        self.manufacturer_info.set_value(device_info.manufacturer)
        self.serial_info.set_value(device_info.serial)
        self.connection_info.set_value(device_info.connection_type)
        
        if device_info.ip_address:
            self.ip_info.set_value(device_info.ip_address)
            self.ip_info.show()
        else:
            self.ip_info.hide()
        
        # System Info
        self.android_version_info.set_value(device_info.android_version)
        self.sdk_version_info.set_value(device_info.sdk_version)
        
        # Hardware Info
        self.screen_resolution_info.set_value(device_info.screen_resolution)
        
        # Battery Info
        self.update_battery_level(device_info.battery_level)
        
        # Enable all groups
        self.device_details_group.setEnabled(True)
        self.system_info_group.setEnabled(True)
        self.hardware_info_group.setEnabled(True)
        self.battery_info_group.setEnabled(True)
        
        logger.info(f"Updated device info for {device_info.model}")
    
    def update_battery_level(self, level):
        """Update battery level display"""
        self.battery_value.setText(f"{level}%")
        self.battery_progress.setValue(level)
        
        # Color coding
        if level > 60:
            color = "#4CAF50"  # Green
        elif level > 20:
            color = "#FFC107"  # Yellow/Orange
        else:
            color = "#F44336"  # Red
        
        self.battery_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #313335;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
    
    def update_extended_info(self, extended_info):
        """
        Update extended device information
        
        Args:
            extended_info: Dictionary with additional device properties
        """
        if not extended_info:
            return
        
        # Update fields that weren't in basic device info
        if 'build_number' in extended_info:
            self.build_info.set_value(extended_info['build_number'])
        
        if 'security_patch' in extended_info:
            self.security_patch_info.set_value(extended_info['security_patch'])
        
        if 'cpu' in extended_info:
            self.cpu_info.set_value(extended_info['cpu'])
        
        if 'ram_total' in extended_info:
            self.ram_info.set_value(extended_info['ram_total'])
        
        if 'storage_total' in extended_info:
            self.storage_info.set_value(extended_info['storage_total'])
        
        if 'battery_status' in extended_info:
            self.battery_status_info.set_value(extended_info['battery_status'])
        
        if 'battery_health' in extended_info:
            self.battery_health_info.set_value(extended_info['battery_health'])
        
        if 'battery_temp' in extended_info:
            temp_c = extended_info['battery_temp']
            self.battery_temp_info.set_value(f"{temp_c}°C")
    
    def show_no_device(self):
        """Show no device selected state"""
        self.model_info.set_value("No device selected")
        self.manufacturer_info.set_value("-")
        self.serial_info.set_value("-")
        self.connection_info.set_value("-")
        self.ip_info.hide()
        
        self.android_version_info.set_value("-")
        self.sdk_version_info.set_value("-")
        self.build_info.set_value("-")
        self.security_patch_info.set_value("-")
        
        self.screen_resolution_info.set_value("-")
        self.cpu_info.set_value("-")
        self.ram_info.set_value("-")
        self.storage_info.set_value("-")
        
        self.update_battery_level(0)
        self.battery_status_info.set_value("-")
        self.battery_health_info.set_value("-")
        self.battery_temp_info.set_value("-")
        
        # Disable groups
        self.device_details_group.setEnabled(False)
        self.system_info_group.setEnabled(False)
        self.hardware_info_group.setEnabled(False)
        self.battery_info_group.setEnabled(False)
