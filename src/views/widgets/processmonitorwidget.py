"""Process monitor widget"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMenu, QMessageBox,
    QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
import logging

from utils.style_loader import load_stylesheet

logger = logging.getLogger(__name__)


class ProcessMonitorWidget(QWidget):
    """Process monitoring interface"""
    
    # Signals
    refresh_requested = pyqtSignal()
    kill_requested = pyqtSignal(int)  # PID
    force_kill_requested = pyqtSignal(int)  # PID
    
    def __init__(self, parent=None):
        super().__init__()
        self.processes = []
        self.filtered_processes = []
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.on_auto_refresh)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup process monitor UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create process table FIRST (before toolbar)
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Process Name", "User", "Memory (MB)", "State", "CPU %"
        ])
        
        # Configure table
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSelectionMode(QTableWidget.SingleSelection)
        self.process_table.setAlternatingRowColors(True)
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_context_menu)
        self.process_table.setSortingEnabled(True)
        
        # Apply table stylesheet
        table_style = load_stylesheet('table_style.qss')
        if table_style:
            self.process_table.setStyleSheet(table_style)
        
        # Set row height
        self.process_table.verticalHeader().setDefaultSectionSize(32)
        self.process_table.verticalHeader().setVisible(False)
        
        # NOW create toolbar (after table exists)
        toolbar = self.create_toolbar()
        layout.addLayout(toolbar)
        
        # Add table to layout
        layout.addWidget(self.process_table)
        
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
        self.search_input.setPlaceholderText("Search processes...")
        self.search_input.textChanged.connect(self.filter_processes)
        self.search_input.setMaximumWidth(250)
        
        # Auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto-refresh (5s)")
        self.auto_refresh_check.stateChanged.connect(self.on_auto_refresh_changed)
        
        # Buttons
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.on_refresh_clicked)
        
        self.kill_btn = QPushButton("❌ Kill Process")
        self.kill_btn.clicked.connect(self.on_kill_clicked)
        self.kill_btn.setEnabled(False)
        
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.auto_refresh_check)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.kill_btn)
        
        # Enable kill button when row selected
        self.process_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        return toolbar
    
    def on_auto_refresh_changed(self, state):
        """Handle auto-refresh toggle"""
        if state == Qt.Checked:
            self.auto_refresh_timer.start(5000)  # 5 seconds
            logger.info("Auto-refresh enabled")
        else:
            self.auto_refresh_timer.stop()
            logger.info("Auto-refresh disabled")
    
    def on_auto_refresh(self):
        """Handle auto-refresh timer"""
        self.refresh_requested.emit()
    
    def on_refresh_clicked(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
    
    def on_kill_clicked(self):
        """Handle kill button click"""
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            if row < len(self.filtered_processes):
                process = self.filtered_processes[row]
                
                reply = QMessageBox.question(
                    self,
                    "Confirm Kill",
                    f"Kill process {process.name} (PID: {process.pid})?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.kill_requested.emit(process.pid)
    
    def on_selection_changed(self):
        """Handle table selection change"""
        has_selection = len(self.process_table.selectedItems()) > 0
        self.kill_btn.setEnabled(has_selection)
    
    def show_context_menu(self, position):
        """Show context menu for process actions"""
        item = self.process_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        if row < 0 or row >= len(self.filtered_processes):
            return
        
        process = self.filtered_processes[row]
        
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
                border: 1px solid #3e3e42;
            }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #094771; }
        """)
        
        kill_action = menu.addAction(f"Kill Process (PID: {process.pid})")
        force_kill_action = menu.addAction(f"Force Kill (SIGKILL)")
        
        action = menu.exec_(self.process_table.mapToGlobal(position))
        
        if action == kill_action:
            self.kill_requested.emit(process.pid)
        elif action == force_kill_action:
            self.force_kill_requested.emit(process.pid)
    
    def update_processes(self, processes):
        """Update process list display"""
        self.processes = processes
        self.filtered_processes = processes.copy()
        self.filter_processes(self.search_input.text())
        self.populate_table()
        
        self.status_label.setText(f"Showing {len(self.filtered_processes)} of {len(processes)} processes")
    
    def filter_processes(self, search_text):
        """Filter processes based on search text"""
        if not search_text:
            self.filtered_processes = self.processes.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_processes = [
                p for p in self.processes
                if search_lower in p.name.lower() or
                   search_lower in str(p.pid) or
                   search_lower in p.user.lower()
            ]
        
        self.populate_table()
        self.status_label.setText(f"Showing {len(self.filtered_processes)} of {len(self.processes)} processes")
    
    def populate_table(self):
        """Populate table with filtered processes"""
        self.process_table.setSortingEnabled(False)
        self.process_table.setRowCount(0)
        
        for process in self.filtered_processes:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)
            
            # PID
            pid_item = QTableWidgetItem(str(process.pid))
            pid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pid_item.setForeground(QColor("#9cdcfe"))
            self.process_table.setItem(row, 0, pid_item)
            
            # Process Name
            name_item = QTableWidgetItem(process.name)
            name_item.setForeground(QColor("#ffffff"))
            self.process_table.setItem(row, 1, name_item)
            
            # User
            user_item = QTableWidgetItem(process.user)
            user_item.setForeground(QColor("#dcdcaa"))
            self.process_table.setItem(row, 2, user_item)
            
            # Memory
            mem_item = QTableWidgetItem(str(process.mem_mb))
            mem_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mem_item.setForeground(QColor("#b5cea8"))
            self.process_table.setItem(row, 3, mem_item)
            
            # State
            state_item = QTableWidgetItem(process.state_text)
            state_item.setTextAlignment(Qt.AlignCenter)
            if process.state == 'R':
                state_item.setForeground(QColor("#4ec9b0"))  # Green for running
            elif process.state == 'Z':
                state_item.setForeground(QColor("#f48771"))  # Red for zombie
            else:
                state_item.setForeground(QColor("#cccccc"))
            self.process_table.setItem(row, 4, state_item)
            
            # CPU % (placeholder)
            cpu_item = QTableWidgetItem("N/A")
            cpu_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            cpu_item.setForeground(QColor("#888888"))
            self.process_table.setItem(row, 5, cpu_item)
        
        self.process_table.setSortingEnabled(True)
    
    def set_device_connected(self, connected):
        """Update UI based on device connection status"""
        self.process_table.setEnabled(connected)
        self.refresh_btn.setEnabled(connected)
        self.search_input.setEnabled(connected)
        self.auto_refresh_check.setEnabled(connected)
        
        if not connected:
            self.process_table.setRowCount(0)
            self.status_label.setText("No device selected")
            self.auto_refresh_timer.stop()
