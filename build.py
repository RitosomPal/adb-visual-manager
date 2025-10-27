"""Build script for creating standalone executable"""

import PyInstaller.__main__
import os
import shutil

# Project name
APP_NAME = "ADB Visual Manager"
MAIN_SCRIPT = "src/main.py"

# PyInstaller options
options = [
    MAIN_SCRIPT,
    f'--name={APP_NAME}',
    '--onedir',  # Create a directory (change to --onefile for single exe)
    '--windowed',  # No console window
    '--clean',
    
    # Add data files
    '--add-data=resources;resources',
    
    # Icon (if you have one)
    # '--icon=resources/icon.ico',
    
    # Exclude unnecessary modules
    '--exclude-module=matplotlib',
    '--exclude-module=pandas',
    '--exclude-module=numpy',
]

print("Building executable...")
PyInstaller.__main__.run(options)

print("\n✅ Build complete!")
print(f"Executable location: dist/{APP_NAME}/")