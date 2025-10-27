"""Application manager widget"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QCheckBox, QHeaderView,
    QMenu, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
import logging

from utils.style_loader import load_stylesheet  # ADD THIS IMPORT

logger = logging.getLogger(__name__)


class AppManagerWidget(QWidget):
    """Application management interface"""
    
    # Signals
    refresh_requested = pyqtSignal(bool)
    install_requested = pyqtSignal(str)
    uninstall_requested = pyqtSignal(str)
    start_requested = pyqtSignal(str)
    stop_requested = pyqtSignal(str)
    clear_data_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.apps = []
        self.filtered_apps = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup app manager UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # App table
        self.app_table = QTableWidget()
        self.app_table.setColumnCount(6)
        self.app_table.setHorizontalHeaderLabels([
            "App Name", "Package", "Version", "Size", "Type", "Status"
        ])
        
        # Configure table
        header = self.app_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.app_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.app_table.setSelectionMode(QTableWidget.SingleSelection)
        self.app_table.setAlternatingRowColors(True)
        self.app_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.app_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # APPLY TABLE STYLESHEET
        table_style = load_stylesheet('table_style.qss')
        if table_style:
            self.app_table.setStyleSheet(table_style)
        
        # Set row height (make rows thinner)
        self.app_table.verticalHeader().setDefaultSectionSize(32)  # Thin rows
        self.app_table.verticalHeader().setVisible(False)  # Hide row numbers
        
        # Enable grid
        self.app_table.setShowGrid(True)
        
        layout.addWidget(self.app_table)
        
        # Status bar
        self.status_label = QLabel("No device selected")
        self.status_label.setStyleSheet("color: #888; padding: 5px; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def create_toolbar(self):
        """Create toolbar with controls"""
        toolbar = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search apps...")
        self.search_input.textChanged.connect(self.filter_apps)
        self.search_input.setMaximumWidth(250)
        
        # Show system apps checkbox
        self.show_system_check = QCheckBox("Show System Apps")
        self.show_system_check.stateChanged.connect(self.on_show_system_changed)
        
        # Buttons
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        
        self.install_btn = QPushButton("Install APK")
        self.install_btn.clicked.connect(self.on_install_clicked)
        
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.show_system_check)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.install_btn)
        
        return toolbar
    
    def on_show_system_changed(self, state):
        """Handle show system apps checkbox change"""
        show_system = state == Qt.Checked
        self.refresh_requested.emit(show_system)
    
    def on_refresh_clicked(self):
        """Handle refresh button click"""
        show_system = self.show_system_check.isChecked()
        self.refresh_requested.emit(show_system)
    
    def on_install_clicked(self):
        """Handle install button click"""
        apk_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select APK File",
            "",
            "APK Files (*.apk);;All Files (*)"
        )
        
        if apk_path:
            self.install_requested.emit(apk_path)
    
    def show_context_menu(self, position):
        """Show context menu for app actions"""
        if self.app_table.rowCount() == 0:
            return
        
        item = self.app_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        if row < 0 or row >= len(self.filtered_apps):
            return
        
        app = self.filtered_apps[row]
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3e3e42;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        # Show running status
        if app.is_running:            
            force_stop_action = menu.addAction("⏹ Force Stop")
            force_stop_action.triggered.connect(lambda: self.stop_requested.emit(app.package_name))
        else:            
            start_action = menu.addAction("▶ Start App")
            start_action.triggered.connect(lambda: self.start_requested.emit(app.package_name))
        
        menu.addSeparator()
        
        # Other actions
        clear_action = menu.addAction("🗑 Clear Data")
        clear_action.triggered.connect(lambda: self.clear_data_requested.emit(app.package_name))
        
        uninstall_action = menu.addAction("❌ Uninstall")
        
        if app.is_system:
            uninstall_action.setEnabled(False)
            uninstall_action.setText("❌ Uninstall (System App)")
        else:
            uninstall_action.triggered.connect(lambda: self._confirm_and_uninstall(app))
        
        menu.exec_(self.app_table.mapToGlobal(position))
    
    def _confirm_and_uninstall(self, app):
        """Confirm and trigger uninstall"""
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall {app.app_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.uninstall_requested.emit(app.package_name)
    
    def update_apps(self, apps):
        """Update app list display"""
        self.apps = apps
        self.filtered_apps = apps.copy()
        self.filter_apps(self.search_input.text())
        self.populate_table()
        
        count = len(apps)
        self.status_label.setText(f"Showing {len(self.filtered_apps)} of {count} apps")
    
    def filter_apps(self, search_text):
        """Filter apps based on search text"""
        if not search_text:
            self.filtered_apps = self.apps.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_apps = [
                app for app in self.apps
                if search_lower in app.app_name.lower() or
                   search_lower in app.package_name.lower()
            ]
        
        self.populate_table()
        self.status_label.setText(f"Showing {len(self.filtered_apps)} of {len(self.apps)} apps")
    
    def populate_table(self):
        """Populate table with filtered apps"""
        self.app_table.setRowCount(0)
        
        for app in self.filtered_apps:
            row = self.app_table.rowCount()
            self.app_table.insertRow(row)
            
            # App Name
            name_item = QTableWidgetItem(app.app_name)
            name_item.setForeground(QColor("#ffffff"))
            self.app_table.setItem(row, 0, name_item)
            
            # Package
            package_item = QTableWidgetItem(app.package_name)
            package_item.setForeground(QColor("#999999"))
            self.app_table.setItem(row, 1, package_item)
            
            # Version
            version_item = QTableWidgetItem(app.version)
            version_item.setForeground(QColor("#cccccc"))
            self.app_table.setItem(row, 2, version_item)
            
            # Size
            size_item = QTableWidgetItem(f"{app.size_mb} MB")
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            size_item.setForeground(QColor("#cccccc"))
            self.app_table.setItem(row, 3, size_item)
            
            # Type
            type_item = QTableWidgetItem(app.app_type)
            if app.is_system:
                type_item.setForeground(QColor("#ce9178"))  # Orange for system
            else:
                type_item.setForeground(QColor("#4ec9b0"))  # Cyan for user
            self.app_table.setItem(row, 4, type_item)
            
            # Status
            status_item = QTableWidgetItem()
            status_item.setTextAlignment(Qt.AlignCenter)
            
            status_font = QFont()
            status_font.setPointSize(9)
            
            if app.is_running:
                # Green emoji for Running
                status_item.setText("🟢 Running")
                status_item.setForeground(QColor("#4ade80"))  # Bright green text
                status_item.setBackground(QColor("#052e16"))  # Dark green background
                status_font.setBold(True)
                status_item.setFont(status_font)
            else:
                # Gray/Red emoji for Stopped
                status_item.setText("⚫ Stopped")
                status_item.setForeground(QColor("#9ca3af"))  # Gray text
                status_item.setBackground(QColor("#1f2937"))  # Dark gray background
                status_item.setFont(status_font)
            
            self.app_table.setItem(row, 5, status_item)
    
    def set_device_connected(self, connected):
        """Update UI based on device connection status"""
        self.app_table.setEnabled(connected)
        self.refresh_btn.setEnabled(connected)
        self.install_btn.setEnabled(connected)
        self.search_input.setEnabled(connected)
        self.show_system_check.setEnabled(connected)
        
        if not connected:
            self.app_table.setRowCount(0)
            self.status_label.setText("No device selected")
