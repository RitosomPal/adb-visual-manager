"""Core ADB connection and device management"""

import logging
from typing import List, Optional
from ppadb.client import Client as AdbClient
from ppadb.device import Device as AdbDevice

from constants import DEFAULT_ADB_HOST, DEFAULT_ADB_PORT, CONNECTION_USB, CONNECTION_NETWORK
from models.devicemodel import DeviceInfo

logger = logging.getLogger(__name__)


class ADBManager:
    """
    Central ADB connection management
    Handles device discovery, connection, and disconnection
    """
    
    def __init__(self, host=DEFAULT_ADB_HOST, port=DEFAULT_ADB_PORT):
        """
        Initialize ADB Manager
        
        Args:
            host: ADB server host address
            port: ADB server port
        """
        self.host = host
        self.port = port
        self.client: Optional[AdbClient] = None
        self._device_cache: dict[str, AdbDevice] = {}
        
        logger.info(f"Initializing ADB Manager (host={host}, port={port})")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ADB client connection"""
        try:
            self.client = AdbClient(host=self.host, port=self.port)
            logger.info("ADB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ADB client: {e}")
            self.client = None
    
    def is_adb_running(self) -> bool:
        """Check if ADB server is running"""
        try:
            if self.client is None:
                return False
            self.client.version()
            return True
        except Exception as e:
            logger.warning(f"ADB server not running: {e}")
            return False
    
    def get_devices(self) -> List[DeviceInfo]:
        """
        Get list of all connected devices
        
        Returns:
            List of DeviceInfo objects
        """
        if not self.is_adb_running():
            logger.warning("Cannot get devices: ADB server not running")
            return []
        
        try:
            devices = self.client.devices()
            device_list = []
            
            for device in devices:
                # Cache device object
                self._device_cache[device.serial] = device
                
                # Get device info
                device_info = self._get_device_info(device)
                device_list.append(device_info)
            
            logger.info(f"Found {len(device_list)} connected device(s)")
            return device_list
            
        except Exception as e:
            logger.error(f"Error getting devices: {e}")
            return []
    
    def _get_device_info(self, device: AdbDevice) -> DeviceInfo:
        """
        Extract detailed information from ADB device
        
        Args:
            device: ADB device object
            
        Returns:
            DeviceInfo object
        """
        try:
            # Get device properties
            model = device.shell("getprop ro.product.model").strip()
            manufacturer = device.shell("getprop ro.product.manufacturer").strip()
            android_version = device.shell("getprop ro.build.version.release").strip()
            sdk_version = device.shell("getprop ro.build.version.sdk").strip()
            
            # Get battery level
            battery_raw = device.shell("dumpsys battery | grep level").strip()
            battery_level = 0
            if "level:" in battery_raw:
                try:
                    battery_level = int(battery_raw.split("level:")[1].strip())
                except:
                    pass
            
            # Get screen resolution
            resolution_raw = device.shell("wm size").strip()
            resolution = "Unknown"
            if "Physical size:" in resolution_raw:
                resolution = resolution_raw.split("Physical size:")[1].strip()
            
            # Determine connection type
            connection_type = CONNECTION_NETWORK if ":" in device.serial else CONNECTION_USB
            ip_address = device.serial.split(":")[0] if connection_type == CONNECTION_NETWORK else None
            
            return DeviceInfo(
                serial=device.serial,
                model=model,
                manufacturer=manufacturer,
                android_version=android_version,
                sdk_version=sdk_version,
                battery_level=battery_level,
                connection_type=connection_type,
                screen_resolution=resolution,
                is_connected=True,
                ip_address=ip_address
            )
            
        except Exception as e:
            logger.warning(f"Error getting device info for {device.serial}: {e}")
            return DeviceInfo(
                serial=device.serial,
                connection_type=CONNECTION_USB,
                is_connected=True
            )
    
    def get_extended_device_info(self, serial: str) -> dict:
        """
        Get extended device information
        
        Args:
            serial: Device serial number
            
        Returns:
            Dictionary with extended device properties
        """
        device = self.get_device_by_serial(serial)
        if not device:
            return {}
        
        try:
            extended_info = {}
            
            # Build information
            build_number = device.shell("getprop ro.build.display.id").strip()
            extended_info['build_number'] = build_number
            
            # Security patch
            security_patch = device.shell("getprop ro.build.version.security_patch").strip()
            extended_info['security_patch'] = security_patch if security_patch else "Unknown"
            
            # CPU info
            cpu_info = device.shell("getprop ro.product.cpu.abi").strip()
            extended_info['cpu'] = cpu_info
            
            # Memory info
            try:
                meminfo = device.shell("cat /proc/meminfo | grep MemTotal").strip()
                if "MemTotal:" in meminfo:
                    mem_kb = int(meminfo.split()[1])
                    mem_gb = round(mem_kb / 1024 / 1024, 1)
                    extended_info['ram_total'] = f"{mem_gb} GB"
            except:
                extended_info['ram_total'] = "Unknown"
            
            # Storage info
            try:
                storage = device.shell("df /data | tail -1").strip()
                parts = storage.split()
                if len(parts) >= 2:
                    total_kb = int(parts[1])
                    total_gb = round(total_kb / 1024 / 1024, 1)
                    extended_info['storage_total'] = f"{total_gb} GB"
            except:
                extended_info['storage_total'] = "Unknown"
            
            # Battery info
            try:
                battery_status_raw = device.shell("dumpsys battery | grep status").strip()
                if "status:" in battery_status_raw:
                    status_code = battery_status_raw.split("status:")[1].strip()
                    status_map = {"1": "Unknown", "2": "Charging", "3": "Discharging", 
                                 "4": "Not charging", "5": "Full"}
                    extended_info['battery_status'] = status_map.get(status_code, "Unknown")
                
                battery_health_raw = device.shell("dumpsys battery | grep health").strip()
                if "health:" in battery_health_raw:
                    health_code = battery_health_raw.split("health:")[1].strip()
                    health_map = {"1": "Unknown", "2": "Good", "3": "Overheat", 
                                 "4": "Dead", "5": "Over voltage", "6": "Unspecified failure", 
                                 "7": "Cold"}
                    extended_info['battery_health'] = health_map.get(health_code, "Unknown")
                
                battery_temp_raw = device.shell("dumpsys battery | grep temperature").strip()
                if "temperature:" in battery_temp_raw:
                    temp_raw = int(battery_temp_raw.split("temperature:")[1].strip())
                    temp_c = round(temp_raw / 10, 1)
                    extended_info['battery_temp'] = temp_c
            except:
                pass
            
            logger.info(f"Retrieved extended info for {serial}")
            return extended_info
            
        except Exception as e:
            logger.error(f"Error getting extended info for {serial}: {e}")
            return {}
    
    def connect_device(self, ip_address: str, port: int = 5555) -> bool:
        """
        Connect to device via network/IP
        
        Args:
            ip_address: Device IP address
            port: Device ADB port (default 5555)
            
        Returns:
            True if connection successful
        """
        if not self.is_adb_running():
            logger.error("Cannot connect: ADB server not running")
            return False
        
        try:
            logger.info(f"Attempting to connect to {ip_address}:{port}")
            result = self.client.remote_connect(ip_address, port)
            
            if result:
                logger.info(f"Successfully connected to {ip_address}:{port}")
                return True
            else:
                logger.warning(f"Failed to connect to {ip_address}:{port}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to {ip_address}:{port}: {e}")
            return False
    
    def disconnect_device(self, device_serial: str) -> bool:
        """
        Disconnect network device
        
        Args:
            device_serial: Device serial number or IP:port
            
        Returns:
            True if disconnection successful
        """
        try:
            logger.info(f"Disconnecting device: {device_serial}")
            
            # Only network devices can be disconnected
            if ":" not in device_serial:
                logger.warning(f"Cannot disconnect USB device: {device_serial}")
                return False
            
            ip_address = device_serial.split(":")[0]
            result = self.client.remote_disconnect(ip_address)
            
            # Remove from cache
            if device_serial in self._device_cache:
                del self._device_cache[device_serial]
            
            logger.info(f"Disconnected from {device_serial}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting {device_serial}: {e}")
            return False
    
    def get_device_by_serial(self, serial: str) -> Optional[AdbDevice]:
        """
        Get ADB device object by serial number
        
        Args:
            serial: Device serial number
            
        Returns:
            ADB device object or None
        """
        if serial in self._device_cache:
            return self._device_cache[serial]
        
        # Refresh device list and try again
        self.get_devices()
        return self._device_cache.get(serial)
    
    def refresh_devices(self) -> List[DeviceInfo]:
        """
        Refresh device list (alias for get_devices)
        
        Returns:
            Updated list of devices
        """
        logger.info("Refreshing device list")
        return self.get_devices()
