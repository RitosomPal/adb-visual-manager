"""Remote control widget with screen preview"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QGroupBox, QMessageBox, QFileDialog, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont, QPixmap
import logging

logger = logging.getLogger(__name__)


class TouchPadWidget(QWidget):
    """Touch pad with live screen preview"""
    
    tap_event = pyqtSignal(int, int)
    swipe_event = pyqtSignal(int, int, int, int)
    refresh_screen_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.device_width = 1080
        self.device_height = 1920
        self.swipe_start = None
        self.swipe_end = None
        self.screen_pixmap = None
        
        # Calculate display size
        self.max_display_height = 350
        self.update_display_size()
        
        # Background
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                border: 2px solid #3e3e42;
                border-radius: 4px;
            }
        """)
    
    def set_device_size(self, width, height):
        """
        Set device screen size
        
        Args:
            width: Device screen width in pixels
            height: Device screen height in pixels
        """
        self.device_width = width
        self.device_height = height
        self.update_display_size()
        logger.info(f"Touch pad set to device size: {width}x{height}")
    
    def update_display_size(self):
        """Update display size based on device aspect ratio"""
        aspect_ratio = self.device_width / self.device_height
        
        display_height = self.max_display_height
        display_width = int(display_height * aspect_ratio)
        
        self.setFixedSize(display_width, display_height)
        logger.info(f"Touch pad display size: {display_width}x{display_height}")
    
    def set_screen_image(self, image_path):
        """
        Set screenshot to display
        
        Args:
            image_path: Path to screenshot image
        """
        try:
            self.screen_pixmap = QPixmap(image_path)
            
            # Scale to fit widget while maintaining aspect ratio
            self.screen_pixmap = self.screen_pixmap.scaled(
                self.width(),
                self.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.update()
            logger.info(f"Screen image loaded: {image_path}")
        except Exception as e:
            logger.error(f"Failed to load screen image: {e}")
            self.screen_pixmap = None
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        self.swipe_start = event.pos()
        self.swipe_end = None
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        if self.swipe_start:
            self.swipe_end = event.pos()
            
            # Check if it's a tap or swipe
            distance = (self.swipe_end - self.swipe_start).manhattanLength()
            
            if distance < 10:
                # Tap
                self.tap_event.emit(event.pos().x(), event.pos().y())
                
                # Request screen refresh after tap
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, self.refresh_screen_requested.emit)
            else:
                # Swipe
                self.swipe_event.emit(
                    self.swipe_start.x(), self.swipe_start.y(),
                    self.swipe_end.x(), self.swipe_end.y()
                )
                
                # Request screen refresh after swipe
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(500, self.refresh_screen_requested.emit)
            
            self.swipe_start = None
            self.swipe_end = None
    
    def paintEvent(self, event):
        """Draw touchpad with screen preview"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw screenshot if available
        if self.screen_pixmap:
            # Draw the screenshot
            x = (self.width() - self.screen_pixmap.width()) // 2
            y = (self.height() - self.screen_pixmap.height()) // 2
            painter.drawPixmap(x, y, self.screen_pixmap)
        else:
            # Draw placeholder text
            painter.setPen(QColor("#888888"))
            font = QFont()
            font.setPointSize(9)
            painter.setFont(font)
            
            aspect = self.device_width / self.device_height
            
            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                f"Device Screen Preview\n"
                f"{self.device_width} × {self.device_height}\n\n"
                f"Aspect: {aspect:.2f}:1\n\n"
                f"Click = Tap\n"
                f"Drag = Swipe\n\n"
                f"Screen will appear after first tap"
            )
        
        # Draw border
        painter.setPen(QColor("#555555"))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)


class RemoteControlWidget(QWidget):
    """Remote control interface"""
    
    # Signals
    tap_requested = pyqtSignal(int, int)
    swipe_requested = pyqtSignal(int, int, int, int)
    text_requested = pyqtSignal(str)
    key_requested = pyqtSignal(str)
    screenshot_requested = pyqtSignal(str)
    auto_refresh_requested = pyqtSignal()
    manual_refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.screen_width = 1080
        self.screen_height = 1920
        self.auto_refresh_enabled = True
        self.setup_ui()
    
    def setup_ui(self):
        """Setup remote control UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel - Touch pad
        left_panel = self.create_touchpad_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Right panel - Controls
        right_panel = self.create_controls_panel()
        main_layout.addWidget(right_panel, 1)
        
        self.setLayout(main_layout)
    
    def create_touchpad_panel(self):
        """Create touch pad panel"""
        group = QGroupBox("Touch Screen Preview")
        layout = QVBoxLayout()
        
        # Touch pad with preview
        self.touchpad = TouchPadWidget()
        self.touchpad.tap_event.connect(self.on_tap)
        self.touchpad.swipe_event.connect(self.on_swipe)
        self.touchpad.refresh_screen_requested.connect(self.on_auto_refresh_screen)  # CHANGED
        layout.addWidget(self.touchpad)
        
        # Controls row
        controls_layout = QHBoxLayout()
        
        # Auto-refresh toggle
        self.auto_refresh_check = QCheckBox("Auto-refresh screen")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self.on_auto_refresh_changed)
        controls_layout.addWidget(self.auto_refresh_check)
        
        controls_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Now")
        refresh_btn.clicked.connect(self.on_refresh_screen)
        controls_layout.addWidget(refresh_btn)
        
        # Screenshot button
        screenshot_btn = QPushButton("📸 Save Screenshot")
        screenshot_btn.clicked.connect(self.on_screenshot_clicked)
        controls_layout.addWidget(screenshot_btn)
        
        layout.addLayout(controls_layout)
        
        group.setLayout(layout)
        return group
    
    def create_controls_panel(self):
        """Create controls panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Text input group
        text_group = self.create_text_input_group()
        layout.addWidget(text_group)
        
        # Hardware buttons group
        hardware_group = self.create_hardware_buttons_group()
        layout.addWidget(hardware_group)
        
        # Volume controls
        volume_group = self.create_volume_group()
        layout.addWidget(volume_group)
        
        # D-Pad (TV remote)
        dpad_group = self.create_dpad_group()
        layout.addWidget(dpad_group)
        
        layout.addStretch()
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)
        
        widget.setLayout(layout)
        return widget
    
    def create_text_input_group(self):
        """Create text input controls"""
        group = QGroupBox("Text Input")
        layout = QVBoxLayout()
        
        # Text field
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Type text to send...")
        self.text_input.returnPressed.connect(self.on_send_text_clicked)
        layout.addWidget(self.text_input)
        
        # Send button
        send_btn = QPushButton("📤 Send Text")
        send_btn.clicked.connect(self.on_send_text_clicked)
        layout.addWidget(send_btn)
        
        group.setLayout(layout)
        return group
    
    def create_hardware_buttons_group(self):
        """Create hardware button controls"""
        group = QGroupBox("Hardware Buttons")
        layout = QGridLayout()
        
        buttons = [
            ("🏠 Home", "HOME", 0, 0),
            ("◀ Back", "BACK", 0, 1),
            ("☰ Menu", "MENU", 1, 0),
            ("⏻ Power", "POWER", 1, 1),
        ]
        
        for label, key, row, col in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, k=key: self.key_requested.emit(k))
            layout.addWidget(btn, row, col)
        
        group.setLayout(layout)
        return group
    
    def create_volume_group(self):
        """Create volume controls"""
        group = QGroupBox("Volume")
        layout = QHBoxLayout()
        
        vol_up = QPushButton("🔊 Up")
        vol_up.clicked.connect(lambda: self.key_requested.emit("VOLUME_UP"))
        
        vol_down = QPushButton("🔉 Down")
        vol_down.clicked.connect(lambda: self.key_requested.emit("VOLUME_DOWN"))
        
        mute = QPushButton("🔇 Mute")
        mute.clicked.connect(lambda: self.key_requested.emit("VOLUME_MUTE"))
        
        layout.addWidget(vol_up)
        layout.addWidget(vol_down)
        layout.addWidget(mute)
        
        group.setLayout(layout)
        return group
    
    def create_dpad_group(self):
        """Create D-Pad controls for TV"""
        group = QGroupBox("D-Pad (TV Remote)")
        layout = QGridLayout()
        
        # D-Pad buttons
        up = QPushButton("▲")
        up.clicked.connect(lambda: self.key_requested.emit("DPAD_UP"))
        layout.addWidget(up, 0, 1)
        
        left = QPushButton("◀")
        left.clicked.connect(lambda: self.key_requested.emit("DPAD_LEFT"))
        layout.addWidget(left, 1, 0)
        
        center = QPushButton("●")
        center.clicked.connect(lambda: self.key_requested.emit("DPAD_CENTER"))
        layout.addWidget(center, 1, 1)
        
        right = QPushButton("▶")
        right.clicked.connect(lambda: self.key_requested.emit("DPAD_RIGHT"))
        layout.addWidget(right, 1, 2)
        
        down = QPushButton("▼")
        down.clicked.connect(lambda: self.key_requested.emit("DPAD_DOWN"))
        layout.addWidget(down, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def on_tap(self, x, y):
        """Handle tap event"""
        # Scale coordinates to device screen
        scale_x = self.screen_width / self.touchpad.width()
        scale_y = self.screen_height / self.touchpad.height()
        
        device_x = int(x * scale_x)
        device_y = int(y * scale_y)
        
        self.status_label.setText(f"Tap at ({device_x}, {device_y})")
        self.tap_requested.emit(device_x, device_y)
    
    def on_swipe(self, x1, y1, x2, y2):
        """Handle swipe event"""
        # Scale coordinates
        scale_x = self.screen_width / self.touchpad.width()
        scale_y = self.screen_height / self.touchpad.height()
        
        dx1 = int(x1 * scale_x)
        dy1 = int(y1 * scale_y)
        dx2 = int(x2 * scale_x)
        dy2 = int(y2 * scale_y)
        
        self.status_label.setText(f"Swipe ({dx1},{dy1}) → ({dx2},{dy2})")
        self.swipe_requested.emit(dx1, dy1, dx2, dy2)
    
    def on_send_text_clicked(self):
        """Handle send text button"""
        text = self.text_input.text().strip()
        if text:
            self.text_requested.emit(text)
            self.text_input.clear()
            self.status_label.setText(f"Sent: {text}")
    
    def on_screenshot_clicked(self):
        """Handle screenshot button"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            "screenshot.png",
            "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            self.screenshot_requested.emit(file_path)
    
    def on_auto_refresh_changed(self, state):
        """Handle auto-refresh toggle"""
        self.auto_refresh_enabled = (state == Qt.Checked)
        logger.info(f"Auto-refresh: {self.auto_refresh_enabled}")
    
    def on_refresh_screen(self):
        """Request screen refresh"""
        self.refresh_screen_requested.emit()
    
    def set_screen_size(self, width, height):
        """Set device screen size for scaling"""
        self.screen_width = width
        self.screen_height = height
        
        # Update touchpad to match device size
        self.touchpad.set_device_size(width, height)
        
        logger.info(f"Screen size set to {width}x{height}")
    
    def update_screen_preview(self, image_path):
        """
        Update screen preview with new screenshot
        
        Args:
            image_path: Path to screenshot file
        """
        self.touchpad.set_screen_image(image_path)
    
    def set_device_connected(self, connected):
        """Update UI based on device connection"""
        self.touchpad.setEnabled(connected)
        self.text_input.setEnabled(connected)
        
        if not connected:
            self.status_label.setText("No device selected")

    def on_auto_refresh_screen(self):
        """Handle auto refresh from touchpad"""
        self.auto_refresh_requested.emit()

    def on_refresh_screen(self):
        """Handle manual refresh button"""
        self.manual_refresh_requested.emit()