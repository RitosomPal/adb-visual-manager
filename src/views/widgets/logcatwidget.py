"""Logcat viewer widget"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QComboBox, QLineEdit, QLabel, QCheckBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LogcatWidget(QWidget):
    """Logcat viewer interface"""
    
    # Signals
    clear_requested = pyqtSignal()
    start_requested = pyqtSignal(str, str)  # level_filter, tag_filter
    stop_requested = pyqtSignal()
    export_requested = pyqtSignal(str)  # file_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_streaming = False
        self.auto_scroll = True
        self.setup_ui()
    
    def setup_ui(self):
        """Setup logcat viewer UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        
        # Set monospace font
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.Monospace)
        self.log_display.setFont(font)
        
        # Dark theme styling
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3e3e42;
            }
        """)
        
        layout.addWidget(self.log_display)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; padding: 5px; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def create_toolbar(self):
        """Create toolbar with controls"""
        toolbar = QHBoxLayout()
        
        # Log level filter
        toolbar.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(['Verbose', 'Debug', 'Info', 'Warning', 'Error', 'Fatal'])
        self.level_combo.setCurrentText('Verbose')
        self.level_combo.setMaximumWidth(100)
        toolbar.addWidget(self.level_combo)
        
        # Tag filter
        toolbar.addWidget(QLabel("Tag:"))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Filter by tag...")
        self.tag_input.setMaximumWidth(150)
        toolbar.addWidget(self.tag_input)
        
        # Search
        toolbar.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search logs...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.on_search_changed)
        toolbar.addWidget(self.search_input)
        
        toolbar.addStretch()
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.stateChanged.connect(self.on_auto_scroll_changed)
        toolbar.addWidget(self.auto_scroll_check)
        
        # Buttons
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.on_start_clicked)
        toolbar.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏸ Stop")
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        toolbar.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.clicked.connect(self.on_export_clicked)
        toolbar.addWidget(self.export_btn)
        
        return toolbar
    
    def on_start_clicked(self):
        """Handle start button"""
        level_map = {
            'Verbose': 'V',
            'Debug': 'D',
            'Info': 'I',
            'Warning': 'W',
            'Error': 'E',
            'Fatal': 'F'
        }
        
        level = level_map.get(self.level_combo.currentText(), 'V')
        tag = self.tag_input.text().strip() or None
        
        self.is_streaming = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Streaming...")
        
        self.start_requested.emit(level, tag)
    
    def on_stop_clicked(self):
        """Handle stop button"""
        self.is_streaming = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
        
        self.stop_requested.emit()
    
    def on_clear_clicked(self):
        """Handle clear button"""
        self.log_display.clear()
        self.clear_requested.emit()
        self.status_label.setText("Logs cleared")
    
    def on_export_clicked(self):
        """Handle export button"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"logcat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.export_requested.emit(file_path)
    
    def on_auto_scroll_changed(self, state):
        """Handle auto-scroll toggle"""
        self.auto_scroll = (state == Qt.Checked)
    
    def on_search_changed(self, text):
        """Handle search text change"""
        # Highlight search matches
        if not text:
            # Clear highlighting
            cursor = self.log_display.textCursor()
            cursor.select(QTextCursor.Document)
            format = QTextCharFormat()
            format.setBackground(QColor("#1e1e1e"))
            cursor.setCharFormat(format)
            return
        
        # Simple search - could be improved
        # This is a basic implementation
        pass
    
    def append_log(self, log_entry):
        """
        Append a log entry to the display
        
        Args:
            log_entry: LogEntry object or string
        """
        # Handle string input (raw log)
        if isinstance(log_entry, str):
            self.log_display.append(log_entry)
            
            # Auto-scroll
            if self.auto_scroll:
                cursor = self.log_display.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.log_display.setTextCursor(cursor)
                self.log_display.ensureCursorVisible()
            return
        
        # Create formatted text for LogEntry object
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set color based on log level
        format = QTextCharFormat()
        format.setForeground(QColor(log_entry.level_color))
        
        cursor.insertText(str(log_entry) + '\n', format)
        
        # Auto-scroll
        if self.auto_scroll:
            self.log_display.setTextCursor(cursor)
            self.log_display.ensureCursorVisible()
    
    def set_device_connected(self, connected):
        """Update UI based on device connection"""
        self.start_btn.setEnabled(connected and not self.is_streaming)
        self.level_combo.setEnabled(connected)
        self.tag_input.setEnabled(connected)
        
        if not connected:
            self.on_stop_clicked()
            self.status_label.setText("No device selected")
