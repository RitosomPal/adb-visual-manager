"""Interactive ADB terminal widget"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QLineEdit, QPushButton, QLabel, QListWidget,
    QSplitter, QMenu, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent
import logging

logger = logging.getLogger(__name__)


class CommandInput(QLineEdit):
    """Custom line edit with command history navigation"""
    
    command_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_history = []
        self.history_index = -1
        self.setPlaceholderText("Enter ADB shell command...")
        
        # Connect return key to submit command
        self.returnPressed.connect(self.submit_command)
    
    def submit_command(self):
        """Submit the current command"""
        command = self.text().strip()
        if command:
            # Add to history
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)
            
            # Emit signal
            self.command_submitted.emit(command)
            
            # Clear input
            self.clear()
            self.history_index = len(self.command_history)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle arrow keys for history navigation"""
        if event.key() == Qt.Key_Up:
            self.navigate_history_up()
        elif event.key() == Qt.Key_Down:
            self.navigate_history_down()
        else:
            super().keyPressEvent(event)
    
    def navigate_history_up(self):
        """Navigate to previous command in history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.setText(self.command_history[self.history_index])
    
    def navigate_history_down(self):
        """Navigate to next command in history"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.setText(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.clear()
    
    def get_history(self):
        """Get command history"""
        return self.command_history.copy()


class TerminalWidget(QWidget):
    """Interactive terminal for ADB shell commands"""
    
    # Signals
    command_entered = pyqtSignal(str)
    clear_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.common_commands = self.get_common_commands()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup terminal UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter for terminal and history
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Terminal
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout()
        terminal_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("ADB Shell Terminal")
        header.setStyleSheet("font-weight: bold; font-size: 12pt; padding: 5px;")
        terminal_layout.addWidget(header)
        
        # Output display
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #555555;
                padding: 5px;
            }
        """)
        terminal_layout.addWidget(self.output_display)
        
        # Command input area
        input_layout = QHBoxLayout()
        
        prompt_label = QLabel("$")
        prompt_label.setStyleSheet("color: #00ff00; font-weight: bold; font-size: 11pt;")
        
        self.command_input = CommandInput()
        self.command_input.command_submitted.connect(self.on_command_submitted)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(lambda: self.command_input.submit_command())
        self.send_btn.setMaximumWidth(80)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_output)
        self.clear_btn.setMaximumWidth(80)
        
        input_layout.addWidget(prompt_label)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.clear_btn)
        
        terminal_layout.addLayout(input_layout)
        
        # Help text
        help_text = QLabel("Tip: Use ↑↓ arrows to navigate command history | Common commands on the right →")
        help_text.setStyleSheet("color: #888; font-size: 8pt; padding: 3px;")
        terminal_layout.addWidget(help_text)
        
        terminal_widget.setLayout(terminal_layout)
        splitter.addWidget(terminal_widget)
        
        # Right side - Command history and quick commands
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # Command history with clear button
        history_header_layout = QHBoxLayout()
        history_label = QLabel("Command History")
        history_label.setStyleSheet("font-weight: bold; padding: 5px;")
        
        self.clear_history_btn = QPushButton("Clear")
        self.clear_history_btn.setMaximumWidth(60)
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        history_header_layout.addWidget(history_label)
        history_header_layout.addStretch()
        history_header_layout.addWidget(self.clear_history_btn)
        sidebar_layout.addLayout(history_header_layout)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.on_history_item_clicked)
        sidebar_layout.addWidget(self.history_list)
        
        # Common commands
        common_label = QLabel("Common Commands (Double-click)")
        common_label.setStyleSheet("font-weight: bold; padding: 5px;")
        sidebar_layout.addWidget(common_label)
        
        self.common_list = QListWidget()
        self.common_list.itemDoubleClicked.connect(self.on_common_command_clicked)
        self.common_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.common_list.customContextMenuRequested.connect(self.show_common_command_menu)
        sidebar_layout.addWidget(self.common_list)
        
        # NOW populate common commands AFTER creating the widget
        self.populate_common_commands()
        
        sidebar_widget.setLayout(sidebar_layout)
        splitter.addWidget(sidebar_widget)
        
        # Set splitter proportions (70% terminal, 30% sidebar)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Show welcome message
        self.show_welcome_message()

    def show_welcome_message(self):
        """Display welcome message"""
        welcome = """
╔══════════════════════════════════════════════════════════╗
║          ADB Shell Terminal - Ready                      ║
╚══════════════════════════════════════════════════════════╝

Connected to device. Enter ADB shell commands below.
Type 'help' for available commands, or 'clear' to clear screen.

"""
        self.output_display.setPlainText(welcome)
    
    def get_common_commands(self):
        """Get list of common ADB commands"""
        return [
            ("ls", "List directory contents"),
            ("ls -la", "List all files with details"),
            ("pwd", "Print working directory"),
            ("cd /sdcard", "Change to SD card directory"),
            ("cat /proc/cpuinfo", "Show CPU information"),
            ("cat /proc/meminfo", "Show memory information"),
            ("df -h", "Show disk usage"),
            ("ps", "List running processes"),
            ("top -n 1", "Show top processes"),
            ("getprop", "List all system properties"),
            ("pm list packages", "List all packages"),
            ("pm list packages -3", "List 3rd party packages"),
            ("dumpsys battery", "Show battery info"),
            ("dumpsys window", "Show window info"),
            ("screencap /sdcard/screenshot.png", "Take screenshot"),
            ("input text 'Hello'", "Send text input"),
            ("input keyevent 3", "Send HOME key"),
            ("reboot", "Reboot device"),
            ("exit", "Exit shell"),
        ]
    
    def populate_common_commands(self):
        """Populate common commands list"""
        for cmd, description in self.common_commands:
            self.common_list.addItem(f"{cmd}   # {description}")
    
    def on_command_submitted(self, command):
        """Handle command submission"""
        # Add to history list
        self.history_list.insertItem(0, command)
        
        # Show command in output
        self.append_output(f"\n$ {command}\n", "#00ffff")
        
        # Handle special commands
        if command.lower() == "clear":
            self.clear_output()
            return
        elif command.lower() == "help":
            self.show_help()
            return
        
        # Emit signal for controller to handle
        self.command_entered.emit(command)
        
        logger.info(f"Command entered: {command}")
    
    def on_history_item_clicked(self, item):
        """Handle history item double-click"""
        command = item.text()
        self.command_input.setText(command)
        self.command_input.setFocus()
    
    def on_common_command_clicked(self, item):
        """Handle common command double-click"""
        # Extract command (before the #)
        full_text = item.text()
        command = full_text.split("#")[0].strip()
        self.command_input.setText(command)
        self.command_input.setFocus()
    
    def append_output(self, text, color="#00ff00"):
        """
        Append text to output display
        
        Args:
            text: Text to append
            color: Text color (hex)
        """
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set color
        format = cursor.charFormat()
        format.setForeground(Qt.GlobalColor(self._hex_to_qt_color(color)))
        cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.output_display.setTextCursor(cursor)
        self.output_display.ensureCursorVisible()
    
    def _hex_to_qt_color(self, hex_color):
        """Convert hex color to Qt color constant (simplified)"""
        color_map = {
            "#00ff00": Qt.green,
            "#00ffff": Qt.cyan,
            "#ff0000": Qt.red,
            "#ffff00": Qt.yellow,
            "#ffffff": Qt.white,
        }
        return color_map.get(hex_color, Qt.green)
    
    def display_output(self, output, is_error=False):
        """
        Display command output
        
        Args:
            output: Command output text
            is_error: True if this is error output
        """
        color = "#ff0000" if is_error else "#00ff00"
        self.append_output(output, color)
    
    def display_error(self, error):
        """Display error message"""
        self.append_output(f"ERROR: {error}\n", "#ff0000")
    
    def clear_output(self):
        """Clear terminal output"""
        self.output_display.clear()
        self.show_welcome_message()
        self.clear_requested.emit()
    
    def show_help(self):
        """Show help text"""
        help_text = """
Available Commands:
  - Any ADB shell command (ls, cd, ps, etc.)
  - 'clear' - Clear terminal screen
  - 'help' - Show this help message
  - Use ↑↓ to navigate command history
  - Double-click common commands on the right to use them

Common ADB Commands:
  ls              - List files
  cd <path>       - Change directory
  cat <file>      - Display file contents
  ps              - List processes
  pm list packages - List installed packages
  getprop         - Show system properties
  dumpsys <service> - Dump system service info

"""
        self.append_output(help_text, "#ffff00")
    
    def set_device_connected(self, connected):
        """
        Update UI based on device connection
        
        Args:
            connected: True if device is connected
        """
        self.command_input.setEnabled(connected)
        self.send_btn.setEnabled(connected)
        
        if not connected:
            self.output_display.clear()
            self.append_output("\n⚠ No device connected\n", "#ff0000")
            self.append_output("Please select a device to use the terminal.\n", "#ffff00")

    def clear_history(self):
        """Clear command history"""
        self.history_list.clear()
        self.command_input.command_history.clear()
        self.command_input.history_index = -1
        self.append_output("\n🗑️ Command history cleared\n", "#ffff00")
        logger.info("Command history cleared")
    
    def show_common_command_menu(self, position):
        """Show context menu for common commands"""
        item = self.common_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        copy_action = menu.addAction("Copy Command")
        use_action = menu.addAction("Use Command")
        
        action = menu.exec_(self.common_list.mapToGlobal(position))
        
        if action == copy_action:
            # Extract command
            full_text = item.text()
            command = full_text.split("#")[0].strip()
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(command)
            self.append_output(f"\n📋 Copied: {command}\n", "#ffff00")
        elif action == use_action:
            self.on_common_command_clicked(item)

