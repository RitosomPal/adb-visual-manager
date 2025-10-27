"""Main application window"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QAction, QMenuBar, QToolBar, QStatusBar, QLabel,
    QMessageBox, QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon

from views.widgets.devicepanel import DevicePanel
from views.widgets.deviceinfo import DeviceInfoWidget
from views.widgets.terminalwidget import TerminalWidget
from views.widgets.appmanagerwidget import AppManagerWidget
from views.widgets.fileexplorerwidget import FileExplorerWidget
from views.widgets.processmonitorwidget import ProcessMonitorWidget
from views.widgets.logcatwidget import LogcatWidget
from views.widgets.remotecontrolwidget import RemoteControlWidget
from constants import (
    APP_NAME, APP_ICON_PATH, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_WIDTH_PERCENT, WINDOW_HEIGHT_PERCENT,
    WINDOW_MAX_WIDTH_PERCENT, WINDOW_MAX_HEIGHT_PERCENT,
    WINDOW_START_MAXIMIZED  
)
from utils.screen_utils import get_optimal_window_size, center_window, get_dpi_scale_factor
import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""
    
    # Signals
    device_selected = pyqtSignal(str)  # device serial
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.apply_responsive_sizing()
    
    def setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle(APP_NAME)
        # icon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'icons', APP_ICON_PATH)
        # print(icon_path)
        self.setWindowIcon(QIcon(APP_ICON_PATH)) 
        
        # Set absolute minimum size
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        # Central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Device panel at top
        self.device_panel = DevicePanel()
        layout.addWidget(self.device_panel)
        
        # Tab widget for main features
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        
        # Create placeholder tabs (will be replaced with actual widgets later)
        self.create_placeholder_tabs()
        
        layout.addWidget(self.tab_widget)
        central_widget.setLayout(layout)
    
    def apply_responsive_sizing(self):
        """Apply responsive window sizing based on screen resolution"""
        # Log DPI information
        scale = get_dpi_scale_factor()
        logger.info(f"Display scale: {int(scale * 100)}%")
        
        # Get optimal size
        optimal_size = get_optimal_window_size(
            min_width=WINDOW_MIN_WIDTH,
            min_height=WINDOW_MIN_HEIGHT,
            width_percent=WINDOW_WIDTH_PERCENT,
            height_percent=WINDOW_HEIGHT_PERCENT,
            max_width_percent=WINDOW_MAX_WIDTH_PERCENT,
            max_height_percent=WINDOW_MAX_HEIGHT_PERCENT
        )
        
        # Resize window
        self.resize(optimal_size)
        
        # Center window on screen (only if not maximizing)
        if not WINDOW_START_MAXIMIZED:
            center_window(self)
        
        # Show maximized if configured
        if WINDOW_START_MAXIMIZED:
            self.showMaximized()
            logger.info("Window opened in maximized mode")
        else:
            logger.info(f"Window sized to {optimal_size.width()}x{optimal_size.height()}")
    
    def create_placeholder_tabs(self):
        """Create tabs for features"""
        # Dashboard tab with device info (ACTUAL IMPLEMENTATION)
        self.dashboard_widget = DeviceInfoWidget()
        scroll_dashboard = QScrollArea()
        scroll_dashboard.setWidgetResizable(True)
        scroll_dashboard.setWidget(self.dashboard_widget)
        self.tab_widget.addTab(scroll_dashboard, "Dashboard")
        
        # Applications tab (ACTUAL IMPLEMENTATION)
        self.app_manager_widget = AppManagerWidget()
        scroll_apps = QScrollArea()
        scroll_apps.setWidgetResizable(True)
        scroll_apps.setWidget(self.app_manager_widget)
        self.tab_widget.addTab(scroll_apps, "Applications")

        # File Explorer tab
        self.file_explorer_widget = FileExplorerWidget()
        self.tab_widget.addTab(self.file_explorer_widget, "File Explorer")

        # Processes tab
        self.process_monitor_widget = ProcessMonitorWidget()
        scroll_processes = QScrollArea()
        scroll_processes.setWidgetResizable(True)
        scroll_processes.setWidget(self.process_monitor_widget)
        self.tab_widget.addTab(scroll_processes, "Processes")
        
        # Terminal tab
        self.terminal_widget = TerminalWidget()
        self.tab_widget.addTab(self.terminal_widget, "Terminal")

        # Logcat tab
        self.logcat_widget = LogcatWidget()
        self.tab_widget.addTab(self.logcat_widget, "Logcat")
        
        # Remote Control tab
        self.remote_control_widget = RemoteControlWidget()
        scroll_remote = QScrollArea()
        scroll_remote.setWidgetResizable(True)
        scroll_remote.setWidget(self.remote_control_widget)
        self.tab_widget.addTab(scroll_remote, "Remote Control")
    
    def setup_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Device menu
        device_menu = menubar.addMenu("&Device")
        
        connect_action = QAction("&Connect...", self)
        connect_action.setShortcut("Ctrl+N")
        connect_action.triggered.connect(self.device_panel.on_connect_clicked)
        device_menu.addAction(connect_action)
        
        disconnect_action = QAction("&Disconnect", self)
        disconnect_action.triggered.connect(self.device_panel.on_disconnect_clicked)
        device_menu.addAction(disconnect_action)
        
        device_menu.addSeparator()
        
        refresh_action = QAction("&Refresh Devices", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.device_panel.on_refresh_clicked)
        device_menu.addAction(refresh_action)
        
        # View menu (NEW)
        view_menu = menubar.addMenu("&View")
        
        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message label
        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message)
        
        # DPI info label (NEW)
        scale = get_dpi_scale_factor()
        self.dpi_label = QLabel(f"Scale: {int(scale * 100)}%")
        self.dpi_label.setStyleSheet("color: #888;")
        self.status_bar.addPermanentWidget(self.dpi_label)
        
        # ADB status label
        self.adb_status_label = QLabel("ADB: Unknown")
        self.status_bar.addPermanentWidget(self.adb_status_label)
    
    def toggle_fullscreen(self, checked):
        """Toggle fullscreen mode"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def show_about(self):
        """Show about dialog"""
        scale = get_dpi_scale_factor()
        from utils.screen_utils import get_screen_geometry
        screen = get_screen_geometry()
        
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            "<p>A comprehensive desktop application for managing Android devices via ADB.</p>"
            "<p>Version 1.0.0</p>"
            "<p>Built with Python and PyQt5</p>"
            "<hr>"
            f"<p><small>Display: {screen.width()}x{screen.height()} @ {int(scale * 100)}% scale<br>"
            f"Window: {self.width()}x{self.height()}</small></p>"
        )
    
    def set_status_message(self, message, timeout=5000):
        """
        Set status bar message
        
        Args:
            message: Status message
            timeout: Display duration in milliseconds
        """
        self.status_message.setText(message)
        if timeout > 0:
            self.status_bar.showMessage(message, timeout)
    
    def set_adb_status(self, connected):
        """
        Update ADB connection status
        
        Args:
            connected: True if ADB is connected
        """
        if connected:
            self.adb_status_label.setText("ADB: Connected")
            self.adb_status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.adb_status_label.setText("ADB: Disconnected")
            self.adb_status_label.setStyleSheet("color: #F44336;")
    
    def show_error(self, title, message):
        """Show error dialog"""
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title, message):
        """Show warning dialog"""
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title, message):
        """Show info dialog"""
        QMessageBox.information(self, title, message)
    
    def confirm_action(self, title, message):
        """
        Show confirmation dialog
        
        Returns:
            True if user confirmed
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
