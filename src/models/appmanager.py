"""Application management model - Production Ready"""

import logging
from typing import List, Optional, Dict
from models.appmodel import AppInfo

logger = logging.getLogger(__name__)


class AppManager:
    """Handle app installation, removal, and status monitoring"""
    
    def __init__(self, adb_manager):
        """
        Initialize app manager
        
        Args:
            adb_manager: ADBManager instance
        """
        self.adb_manager = adb_manager
        self._running_cache = {}  # Cache running status
        logger.info("App manager initialized")
    
    def list_installed_apps(self, device_serial: str, show_system: bool = False) -> List[AppInfo]:
        """
        List all installed applications
        
        Args:
            device_serial: Device serial number
            show_system: Include system apps
            
        Returns:
            List of AppInfo objects sorted by app name
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            logger.error(f"Device {device_serial} not found")
            return []
        
        try:
            apps = []
            
            # Get package list based on type
            if show_system:
                cmd = "pm list packages -s"  # System apps
                logger.info("Loading system apps...")
            else:
                cmd = "pm list packages -3"  # Third-party apps
                logger.info("Loading user apps...")
            
            package_output = device.shell(cmd).strip()
            if not package_output:
                logger.warning("No packages found")
                return []
            
            package_list = [
                line.replace("package:", "").strip() 
                for line in package_output.split('\n') 
                if line.startswith("package:")
            ]
            
            total = len(package_list)
            logger.info(f"Found {total} packages")
            
            # Get all running packages in one batch (much faster)
            running_packages = self._get_running_packages_batch(device)
            
            # Process each package
            for idx, package_name in enumerate(package_list, 1):
                if not package_name:
                    continue
                
                # Progress logging every 20 packages
                if idx % 20 == 0 or idx == total:
                    logger.info(f"Processing {idx}/{total} packages...")
                
                # Check if running from batch result
                is_running = package_name in running_packages
                
                # Get detailed info
                app_info = self._get_app_info_fast(
                    device, 
                    package_name, 
                    is_running, 
                    show_system
                )
                
                if app_info:
                    apps.append(app_info)
            
            # Sort by app name
            apps.sort(key=lambda x: x.app_name.lower())
            
            logger.info(f"Successfully loaded {len(apps)} apps")
            return apps
            
        except Exception as e:
            logger.error(f"Error listing apps: {e}", exc_info=True)
            return []
    
    def _get_running_packages_batch(self, device) -> set:
        """
        Get all running packages in one batch operation (FAST)
        
        Args:
            device: ADB device instance
            
        Returns:
            Set of running package names
        """
        running = set()
        
        try:
            # Get all running processes
            ps_output = device.shell("ps -A").strip()
            
            if not ps_output:
                # Fallback to simple ps
                ps_output = device.shell("ps").strip()
            
            # Parse ps output
            for line in ps_output.split('\n')[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 9:
                    # Last column is usually package/process name
                    process_name = parts[-1]
                    
                    # Only keep app package names (contain dots, not paths)
                    if '.' in process_name and not process_name.startswith('/'):
                        running.add(process_name)
            
            logger.info(f"Found {len(running)} running processes")
            return running
            
        except Exception as e:
            logger.error(f"Error getting running packages: {e}")
            return set()
    
    def _get_app_info_fast(self, device, package_name: str, is_running: bool, is_system: bool) -> Optional[AppInfo]:
        """
        Get app info with minimal ADB calls (OPTIMIZED)
        
        Args:
            device: ADB device instance
            package_name: Package name
            is_running: Whether app is running
            is_system: Whether this is a system app
            
        Returns:
            AppInfo object or None
        """
        try:
            # Get version info using single dumpsys call
            dumpsys = device.shell(f"dumpsys package {package_name}").strip()
            
            version = "Unknown"
            version_code = "Unknown"
            is_enabled = True
            
            # Parse dumpsys output efficiently
            for line in dumpsys.split('\n'):
                line_stripped = line.strip()
                
                if 'versionName=' in line_stripped and version == "Unknown":
                    try:
                        version = line_stripped.split('versionName=')[1].split()[0]
                    except:
                        pass
                
                elif 'versionCode=' in line_stripped and version_code == "Unknown":
                    try:
                        version_code = line_stripped.split('versionCode=')[1].split()[0]
                    except:
                        pass
                
                elif 'enabled=' in line_stripped:
                    is_enabled = '=1' in line_stripped or '=true' in line_stripped.lower()
            
            # Use package name as app name (fast, good enough)
            app_name = package_name.split('.')[1].title()
            
            return AppInfo(
                package_name=package_name,
                app_name=app_name,
                version=version,
                version_code=version_code,
                size=0,  # Skip for performance
                is_system=is_system,
                is_running=is_running,
                is_enabled=is_enabled
            )
            
        except Exception as e:
            logger.debug(f"Error getting info for {package_name}: {e}")
            return None
    
    def get_app_info(self, device_serial: str, package_name: str, is_running: bool = None, is_system: bool = None) -> Optional[AppInfo]:
        """
        Get detailed app info for a single app
        
        Args:
            device_serial: Device serial number
            package_name: Package name
            is_running: Running status (if known)
            is_system: System app flag (if known)
            
        Returns:
            AppInfo object or None
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return None
        
        # Determine running status if not provided
        if is_running is None:
            is_running = self.is_app_running(device_serial, package_name)
        
        # Determine system status if not provided
        if is_system is None:
            try:
                path = device.shell(f"pm path {package_name}").strip()
                is_system = '/system/' in path or '/vendor/' in path
            except:
                is_system = False
        
        return self._get_app_info_fast(device, package_name, is_running, is_system)
    
    def is_app_running(self, device_serial: str, package_name: str) -> bool:
        """
        Check if app is running using pidof (MOST RELIABLE)
        
        Args:
            device_serial: Device serial number
            package_name: Package name
            
        Returns:
            True if running
        """
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            # pidof returns PID if running, empty if not
            pid = device.shell(f"pidof {package_name}").strip()
            is_running = bool(pid and len(pid) > 0)
            
            logger.debug(f"{package_name}: {'RUNNING' if is_running else 'NOT RUNNING'}")
            return is_running
            
        except Exception as e:
            logger.debug(f"Error checking {package_name}: {e}")
            return False
    
    def install_apk(self, device_serial: str, apk_path: str) -> bool:
        """Install APK file"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Installing: {apk_path}")
            device.install(apk_path)
            logger.info("Installation successful")
            return True
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            return False
    
    def uninstall_app(self, device_serial: str, package_name: str) -> bool:
        """Uninstall app"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Uninstalling: {package_name}")
            device.uninstall(package_name)
            logger.info("Uninstallation successful")
            return True
        except Exception as e:
            logger.error(f"Uninstall failed: {e}")
            return False
    
    def start_app(self, device_serial: str, package_name: str) -> bool:
        """Launch app"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Starting: {package_name}")
            result = device.shell(f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1")
            
            success = "Events injected" in result or "No activities found" not in result
            if success:
                logger.info("App started")
            else:
                logger.warning("Failed to start app")
            
            return success
        except Exception as e:
            logger.error(f"Start failed: {e}")
            return False
    
    def stop_app(self, device_serial: str, package_name: str) -> bool:
        """Force stop app"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Stopping: {package_name}")
            device.shell(f"am force-stop {package_name}")
            logger.info("App stopped")
            return True
        except Exception as e:
            logger.error(f"Stop failed: {e}")
            return False
    
    def clear_app_data(self, device_serial: str, package_name: str) -> bool:
        """Clear app data and cache"""
        device = self.adb_manager.get_device_by_serial(device_serial)
        if not device:
            return False
        
        try:
            logger.info(f"Clearing data: {package_name}")
            result = device.shell(f"pm clear {package_name}")
            success = "Success" in result
            
            if success:
                logger.info("Data cleared")
            else:
                logger.warning("Failed to clear data")
            
            return success
        except Exception as e:
            logger.error(f"Clear data failed: {e}")
            return False
