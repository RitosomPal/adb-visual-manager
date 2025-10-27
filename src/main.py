"""ADB Visual Manager - Main Entry Point"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from utils.logger import setup_logging
from models.adbmanager import ADBManager
from controllers.maincontroller import MainController
from constants import APP_NAME, ORGANIZATION
from utils.style_loader import load_combined_stylesheets

def main():
    """Application entry point"""
    # Setup logging
    logger = setup_logging()
    logger.info(f"Starting {APP_NAME}")
    
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION)
    
    # Load dark theme
    stylesheet = load_combined_stylesheets("darktheme.qss", "table_style.qss", "tree_style.qss")
    app.setStyleSheet(stylesheet)
    
    # Initialize ADB Manager
    logger.info("Initializing ADB Manager")
    adb_manager = ADBManager()
    
    # Initialize Main Controller
    main_controller = MainController(adb_manager)
    main_controller.initialize()
    
    # Run application
    logger.info("Application started")
    exit_code = app.exec_()
    
    # Cleanup
    main_controller.shutdown()
    logger.info("Application closed")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
