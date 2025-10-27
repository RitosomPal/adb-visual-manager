"""Build single-file executable with embedded resources"""

import os
import sys
import shutil
import subprocess

APP_NAME = "ADB_Visual_Manager"

print("=" * 60)
print("Building Single-File Executable")
print("=" * 60)

# Step 1: Clean
print("\n1. Cleaning...")
for folder in ['build', 'dist', '__pycache__']:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# Step 2: Build single file
print("\n2. Building single executable...")

cmd = [
    'pyinstaller',
    '--name=' + APP_NAME,
    '--onefile',  # THIS IS THE KEY - single file
    '--windowed',
    '--clean',
    '--noconfirm',
    '--icon=resources/icons/icon.ico',
    '--paths=src',
    # Add resources as data (embedded in .exe)
    '--add-data=resources/*{}resources'.format(';' if os.name == 'nt' else ':'),
    'src/main.py'
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ Build failed:\n{result.stderr}")
    sys.exit(1)

# Step 3: Verify
exe_path = f"dist/{APP_NAME}.exe"

if not os.path.exists(exe_path):
    print(f"❌ Executable not found: {exe_path}")
    sys.exit(1)

file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB

print("\n" + "=" * 60)
print("✅ BUILD SUCCESSFUL!")
print("=" * 60)
print(f"\nSingle executable:")
print(f"  {os.path.abspath(exe_path)}")
print(f"\nFile size: {file_size:.2f} MB")
print(f"\nTo run:")
print(f"  {exe_path}")
print("=" * 60)
