"""File explorer widget with dual-pane file browser"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QLineEdit, QSplitter, QMenu, QFileDialog,
    QMessageBox, QInputDialog, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QFont
import logging
import os

from utils.style_loader import load_stylesheet

logger = logging.getLogger(__name__)


class FileExplorerWidget(QWidget):
    """File explorer with device and local file browsers"""
    
    # Signals
    path_changed = pyqtSignal(str)  # Device path changed
    upload_requested = pyqtSignal(str, str)  # local_path, remote_path
    download_requested = pyqtSignal(str, str)  # remote_path, local_path
    delete_requested = pyqtSignal(str, bool)  # path, is_directory
    rename_requested = pyqtSignal(str, str)  # old_path, new_path
    create_folder_requested = pyqtSignal(str)  # path
    show_hidden_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device_path = "/sdcard"
        self.current_local_path = os.path.expanduser("~")
        self.setup_ui()
    
    def setup_ui(self):
        """Setup file explorer UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Main splitter for dual-pane view
        splitter = QSplitter(Qt.Horizontal)
        
        # Device browser (left)
        device_browser = self.create_device_browser()
        splitter.addWidget(device_browser)
        
        # Local browser (right)
        local_browser = self.create_local_browser()
        splitter.addWidget(local_browser)
        
        # Set equal proportions
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
        
        # Transfer status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def create_device_browser(self):
        """Create device file browser panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("📱 Device Storage")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        header.setFont(header_font)
        header.setStyleSheet("padding: 5px; background-color: #2d2d30;")
        layout.addWidget(header)
        
        # Quick access bookmarks with Show Hidden toggle
        bookmarks_layout = QHBoxLayout()
        bookmarks_layout.setContentsMargins(5, 5, 5, 5)
        
        bookmark_label = QLabel("Quick:")
        bookmark_label.setStyleSheet("font-size: 9pt;")
        bookmarks_layout.addWidget(bookmark_label)
        
        # Common paths - SMALLER BUTTONS
        common_paths = [
            ("📱 SD", "/sdcard"),
            ("📂 DL", "/sdcard/Download"),
            ("📷 DCIM", "/sdcard/DCIM"),
            ("🎵 Music", "/sdcard/Music"),
            ("🖼️ Pics", "/sdcard/Pictures"),
        ]
        
        for label, path in common_paths:
            btn = QPushButton(label)
            btn.setMaximumWidth(70)  # REDUCED from 100
            btn.setMaximumHeight(25)  # ADD height limit
            btn.setStyleSheet("font-size: 8pt; padding: 2px 4px;")  # ADD smaller font
            btn.clicked.connect(lambda checked, p=path: self.navigate_to_path(p))
            bookmarks_layout.addWidget(btn)
        
        bookmarks_layout.addStretch()
        
        # Show Hidden Files checkbox
        self.show_hidden_check = QCheckBox("Show Hidden")
        self.show_hidden_check.setChecked(False)
        self.show_hidden_check.setStyleSheet("font-size: 9pt;")
        self.show_hidden_check.stateChanged.connect(self.on_show_hidden_changed)
        bookmarks_layout.addWidget(self.show_hidden_check)
        
        layout.addLayout(bookmarks_layout)
        
        # Path navigation
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(5, 5, 5, 5)
        
        self.device_path_input = QLineEdit()
        self.device_path_input.setText(self.current_device_path)
        self.device_path_input.returnPressed.connect(self.on_device_path_entered)
        
        go_btn = QPushButton("Go")
        go_btn.clicked.connect(self.on_device_path_entered)
        go_btn.setMaximumWidth(50)
        
        up_btn = QPushButton("↑ Up")
        up_btn.clicked.connect(self.on_device_up_clicked)
        up_btn.setMaximumWidth(60)
        
        path_layout.addWidget(QLabel("Path:"))
        path_layout.addWidget(self.device_path_input)
        path_layout.addWidget(go_btn)
        path_layout.addWidget(up_btn)
        layout.addLayout(path_layout)
        
        # File tree
        self.device_tree = QTreeWidget()
        self.device_tree.setHeaderLabels(["Name", "Size", "Type", "Permissions"])
        self.device_tree.setAlternatingRowColors(True)
        self.device_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_tree.customContextMenuRequested.connect(self.show_device_context_menu)
        self.device_tree.itemDoubleClicked.connect(self.on_device_item_double_clicked)
        
        # Apply tree stylesheet
        tree_style = load_stylesheet('tree_style.qss')  # Reuse table style
        if tree_style:
            self.device_tree.setStyleSheet(tree_style)
        
        # Set column widths
        self.device_tree.setColumnWidth(0, 250)
        self.device_tree.setColumnWidth(1, 100)
        self.device_tree.setColumnWidth(2, 80)
        
        layout.addWidget(self.device_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_device_btn = QPushButton("🔄 Refresh")
        self.refresh_device_btn.clicked.connect(lambda: self.path_changed.emit(self.current_device_path))
        
        self.new_folder_btn = QPushButton("📁 New Folder")
        self.new_folder_btn.clicked.connect(self.on_new_folder_clicked)
        
        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.clicked.connect(self.on_download_clicked)
        
        button_layout.addWidget(self.refresh_device_btn)
        button_layout.addWidget(self.new_folder_btn)
        button_layout.addWidget(self.download_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_local_browser(self):
        """Create local file browser panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("💻 Local Computer")
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        header.setFont(header_font)
        header.setStyleSheet("padding: 5px; background-color: #2d2d30;")
        layout.addWidget(header)
        
        # Path navigation
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(5, 5, 5, 5)
        
        self.local_path_input = QLineEdit()
        self.local_path_input.setText(self.current_local_path)
        self.local_path_input.returnPressed.connect(self.on_local_path_entered)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.on_browse_local_clicked)
        browse_btn.setMaximumWidth(70)
        
        up_btn = QPushButton("↑ Up")
        up_btn.clicked.connect(self.on_local_up_clicked)
        up_btn.setMaximumWidth(60)
        
        path_layout.addWidget(QLabel("Path:"))
        path_layout.addWidget(self.local_path_input)
        path_layout.addWidget(browse_btn)
        path_layout.addWidget(up_btn)
        layout.addLayout(path_layout)
        
        # File tree
        self.local_tree = QTreeWidget()
        self.local_tree.setHeaderLabels(["Name", "Size", "Type"])
        self.local_tree.setAlternatingRowColors(True)
        self.local_tree.itemDoubleClicked.connect(self.on_local_item_double_clicked)
        
        # Apply tree stylesheet
        tree_style = load_stylesheet('tree_style.qss')
        if tree_style:
            self.local_tree.setStyleSheet(tree_style)
        
        # Set column widths
        self.local_tree.setColumnWidth(0, 250)
        self.local_tree.setColumnWidth(1, 100)
        
        layout.addWidget(self.local_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_local_btn = QPushButton("🔄 Refresh")
        self.refresh_local_btn.clicked.connect(self.refresh_local_files)
        
        self.upload_btn = QPushButton("⬆ Upload")
        self.upload_btn.clicked.connect(self.on_upload_clicked)
        
        button_layout.addWidget(self.refresh_local_btn)
        button_layout.addWidget(self.upload_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def on_device_path_entered(self):
        """Handle device path entered"""
        new_path = self.device_path_input.text().strip()
        if new_path:
            self.current_device_path = new_path
            self.path_changed.emit(new_path)
    
    def on_device_up_clicked(self):
        """Navigate up in device directory"""
        if self.current_device_path != "/":
            parent = os.path.dirname(self.current_device_path)
            if not parent:
                parent = "/"
            self.current_device_path = parent
            self.device_path_input.setText(parent)
            self.path_changed.emit(parent)
    
    def on_local_path_entered(self):
        """Handle local path entered"""
        new_path = self.local_path_input.text().strip()
        if new_path and os.path.exists(new_path):
            self.current_local_path = new_path
            self.refresh_local_files()
    
    def on_browse_local_clicked(self):
        """Browse for local directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            self.current_local_path
        )
        if path:
            self.current_local_path = path
            self.local_path_input.setText(path)
            self.refresh_local_files()
    
    def on_local_up_clicked(self):
        """Navigate up in local directory"""
        parent = os.path.dirname(self.current_local_path)
        if parent and os.path.exists(parent):
            self.current_local_path = parent
            self.local_path_input.setText(parent)
            self.refresh_local_files()
    
    def on_device_item_double_clicked(self, item, column):
        """Handle double-click on device item"""
        if item.data(0, Qt.UserRole):  # Check if it's a directory
            file_item = item.data(0, Qt.UserRole + 1)
            if file_item.is_directory:
                self.current_device_path = file_item.path
                self.device_path_input.setText(file_item.path)
                self.path_changed.emit(file_item.path)
    
    def on_local_item_double_clicked(self, item, column):
        """Handle double-click on local item"""
        path = item.data(0, Qt.UserRole)
        if path and os.path.isdir(path):
            self.current_local_path = path
            self.local_path_input.setText(path)
            self.refresh_local_files()
    
    def show_device_context_menu(self, position):
        """Show context menu for device files"""
        item = self.device_tree.itemAt(position)
        if not item:
            return
        
        file_item = item.data(0, Qt.UserRole + 1)
        if not file_item:
            return
        
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
        
        download_action = menu.addAction("⬇ Download")
        rename_action = menu.addAction("✏️ Rename")
        delete_action = menu.addAction("🗑 Delete")
        
        action = menu.exec_(self.device_tree.mapToGlobal(position))
        
        if action == download_action:
            self.download_file(file_item)
        elif action == rename_action:
            self.rename_file(file_item)
        elif action == delete_action:
            self.delete_file(file_item)
    
    def on_new_folder_clicked(self):
        """Create new folder on device"""
        name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Enter folder name:"
        )
        
        if ok and name:
            new_path = f"{self.current_device_path}/{name}"
            self.create_folder_requested.emit(new_path)
    
    def on_download_clicked(self):
        """Download selected file"""
        selected = self.device_tree.selectedItems()
        if selected:
            file_item = selected[0].data(0, Qt.UserRole + 1)
            if file_item:
                self.download_file(file_item)
    
    def on_upload_clicked(self):
        """Upload selected file"""
        selected = self.local_tree.selectedItems()
        if selected:
            local_path = selected[0].data(0, Qt.UserRole)
            if local_path and os.path.isfile(local_path):
                filename = os.path.basename(local_path)
                remote_path = f"{self.current_device_path}/{filename}"
                self.upload_requested.emit(local_path, remote_path)
    
    def download_file(self, file_item):
        """Download file from device"""
        if file_item.is_directory:
            QMessageBox.warning(self, "Not Supported", "Directory download not yet implemented")
            return
        
        local_path = os.path.join(self.current_local_path, file_item.name)
        self.download_requested.emit(file_item.path, local_path)
    
    def rename_file(self, file_item):
        """Rename file on device"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            "Enter new name:",
            text=file_item.name
        )
        
        if ok and new_name:
            parent = os.path.dirname(file_item.path)
            new_path = f"{parent}/{new_name}"
            self.rename_requested.emit(file_item.path, new_path)
    
    def delete_file(self, file_item):
        """Delete file from device"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {file_item.name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.delete_requested.emit(file_item.path, file_item.is_directory)
    
    def update_device_files(self, files):
        """Update device file tree"""
        from PyQt5.QtGui import QFont
        
        self.device_tree.clear()
        
        for file_item in files:
            item = QTreeWidgetItem()

            # Check if hidden
            is_hidden = file_item.name.startswith('.')
            
            # Name with icon and better colors
            if file_item.is_directory:
                if file_item.is_symlink:
                    item.setText(0, f"🔗 {file_item.name}")
                    item.setForeground(0, QColor("#9cdcfe"))  # Light blue for symlinks
                else:
                    item.setText(0, f"📁 {file_item.name}")
                    item.setForeground(0, QColor("#60a5fa"))  # Blue for folders
            else:
                # Different icons based on file type
                name = file_item.name.lower()
                if name.endswith(('.jpg', '.png', '.gif', '.bmp')):
                    item.setText(0, f"🖼️ {file_item.name}")
                    item.setForeground(0, QColor("#f59e0b"))  # Orange for images
                elif name.endswith(('.mp4', '.avi', '.mkv', '.mov')):
                    item.setText(0, f"🎬 {file_item.name}")
                    item.setForeground(0, QColor("#ec4899"))  # Pink for videos
                elif name.endswith(('.mp3', '.wav', '.flac')):
                    item.setText(0, f"🎵 {file_item.name}")
                    item.setForeground(0, QColor("#8b5cf6"))  # Purple for audio
                elif name.endswith(('.apk',)):
                    item.setText(0, f"📦 {file_item.name}")
                    item.setForeground(0, QColor("#10b981"))  # Green for APK
                elif name.endswith(('.zip', '.rar', '.7z', '.tar', '.gz')):
                    item.setText(0, f"📚 {file_item.name}")
                    item.setForeground(0, QColor("#f59e0b"))  # Orange for archives
                else:
                    item.setText(0, f"📄 {file_item.name}")
                    item.setForeground(0, QColor("#d1d5db"))  # Light gray for files

            # Make hidden files slightly italic
            if is_hidden:
                font = item.font(0)
                font.setItalic(True)
                item.setFont(0, font)
            
            # Size with better formatting
            if not file_item.is_directory:
                item.setText(1, file_item.size_formatted)
                item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                item.setForeground(1, QColor("#9ca3af"))
            else:
                item.setText(1, "")
            
            # Type
            item.setText(2, file_item.file_type)
            item.setForeground(2, QColor("#6b7280"))
            
            # Permissions
            item.setText(3, file_item.permissions)
            item.setForeground(3, QColor("#4b5563"))
            
            # Store file item data
            item.setData(0, Qt.UserRole, file_item.is_directory)
            item.setData(0, Qt.UserRole + 1, file_item)
            
            self.device_tree.addTopLevelItem(item)
        
        self.status_label.setText(f"Device: {len(files)} items in {self.current_device_path}")

    def refresh_local_files(self):
        """Refresh local file tree"""
        self.local_tree.clear()
        
        try:
            entries = os.listdir(self.current_local_path)
            
            # Sort: directories first
            dirs = []
            files = []
            
            for entry in entries:
                full_path = os.path.join(self.current_local_path, entry)
                if os.path.isdir(full_path):
                    dirs.append((entry, full_path))
                else:
                    files.append((entry, full_path))
            
            dirs.sort(key=lambda x: x[0].lower())
            files.sort(key=lambda x: x[0].lower())
            
            # Add directories
            for name, path in dirs:
                item = QTreeWidgetItem()
                item.setText(0, f"📁 {name}")
                item.setForeground(0, QColor("#60a5fa"))
                item.setData(0, Qt.UserRole, path)
                self.local_tree.addTopLevelItem(item)
            
            # Add files
            for name, path in files:
                item = QTreeWidgetItem()
                item.setText(0, f"📄 {name}")
                item.setForeground(0, QColor("#cccccc"))
                
                # Size
                try:
                    size = os.path.getsize(path)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{round(size/1024, 2)} KB"
                    else:
                        size_str = f"{round(size/(1024*1024), 2)} MB"
                    item.setText(1, size_str)
                    item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
                except:
                    pass
                
                # Type
                if '.' in name:
                    ext = name.split('.')[-1].upper()
                    item.setText(2, f"{ext} File")
                else:
                    item.setText(2, "File")
                
                item.setData(0, Qt.UserRole, path)
                self.local_tree.addTopLevelItem(item)
            
            self.status_label.setText(f"Local: {len(entries)} items")
            
        except Exception as e:
            logger.error(f"Error listing local files: {e}")
    
    def set_device_connected(self, connected):
        """Update UI based on device connection"""
        self.device_tree.setEnabled(connected)
        self.device_path_input.setEnabled(connected)
        self.refresh_device_btn.setEnabled(connected)
        self.new_folder_btn.setEnabled(connected)
        self.download_btn.setEnabled(connected)
        self.upload_btn.setEnabled(connected)
        
        if not connected:
            self.device_tree.clear()
            self.status_label.setText("No device connected")

    def navigate_to_path(self, path):
        """
        Navigate to a specific path
        
        Args:
            path: Path to navigate to
        """
        self.current_device_path = path
        self.device_path_input.setText(path)
        self.path_changed.emit(path)
    
    def on_show_hidden_changed(self, state):
        """Handle show hidden files checkbox change"""
        from PyQt5.QtCore import Qt
        
        show_hidden = (state == Qt.Checked)
        logger.info(f"Show hidden files: {show_hidden}")
        
        # Emit signal to controller
        self.show_hidden_changed.emit(show_hidden)
        
        # Refresh current path
        if self.current_device_path:
            self.path_changed.emit(self.current_device_path)
