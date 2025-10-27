"""Screen and display utilities for responsive UI"""

from PyQt5.QtWidgets import QDesktopWidget, QApplication
from PyQt5.QtCore import QRect, QSize
import logging

logger = logging.getLogger(__name__)


def get_screen_geometry():
    """
    Get available screen geometry
    
    Returns:
        QRect: Available screen geometry
    """
    desktop = QDesktopWidget()
    screen = desktop.availableGeometry()
    
    logger.info(f"Screen geometry: {screen.width()}x{screen.height()}")
    return screen


def get_optimal_window_size(min_width=800, min_height=600, 
                           width_percent=0.70, height_percent=0.75,
                           max_width_percent=0.90, max_height_percent=0.85):
    """
    Calculate optimal window size based on screen resolution
    
    Args:
        min_width: Minimum window width
        min_height: Minimum window height
        width_percent: Preferred width as percentage of screen
        height_percent: Preferred height as percentage of screen
        max_width_percent: Maximum width as percentage of screen
        max_height_percent: Maximum height as percentage of screen
    
    Returns:
        QSize: Optimal window size
    """
    screen = get_screen_geometry()
    
    # Calculate preferred size
    preferred_width = int(screen.width() * width_percent)
    preferred_height = int(screen.height() * height_percent)
    
    # Calculate maximum size
    max_width = int(screen.width() * max_width_percent)
    max_height = int(screen.height() * max_height_percent)
    
    # Ensure within bounds
    width = max(min_width, min(preferred_width, max_width))
    height = max(min_height, min(preferred_height, max_height))
    
    logger.info(f"Optimal window size: {width}x{height}")
    return QSize(width, height)


def center_window(window):
    """
    Center window on screen
    
    Args:
        window: QWidget to center
    """
    screen = get_screen_geometry()
    window_geometry = window.frameGeometry()
    center_point = screen.center()
    window_geometry.moveCenter(center_point)
    window.move(window_geometry.topLeft())


def get_dpi_scale_factor():
    """
    Get current DPI scale factor
    
    Returns:
        float: DPI scale factor (1.0 = 100%, 1.5 = 150%, etc.)
    """
    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        dpi = screen.logicalDotsPerInch()
        # Standard DPI is 96
        scale = dpi / 96.0
        logger.info(f"DPI scale factor: {scale:.2f} ({int(scale * 100)}%)")
        return scale
    return 1.0


def is_high_dpi():
    """
    Check if running on high DPI display
    
    Returns:
        bool: True if DPI scaling > 125%
    """
    return get_dpi_scale_factor() > 1.25
