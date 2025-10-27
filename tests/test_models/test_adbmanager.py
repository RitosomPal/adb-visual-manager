"""Unit tests for ADB Manager"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from models.adbmanager import ADBManager
from models.devicemodel import DeviceInfo

class TestADBManager(unittest.TestCase):
    """Test ADB Manager functionality"""
    
    @patch('models.adbmanager.AdbClient')
    def test_initialization(self, mock_client):
        """Test ADB Manager initialization"""
        adb_manager = ADBManager()
        
        self.assertIsNotNone(adb_manager)
        self.assertEqual(adb_manager.host, "127.0.0.1")
        self.assertEqual(adb_manager.port, 5037)
        mock_client.assert_called_once()
    
    @patch('models.adbmanager.AdbClient')
    def test_connect_device_success(self, mock_client):
        """Test successful device connection"""
        mock_client.return_value.remote_connect.return_value = True
        mock_client.return_value.version.return_value = "1.0.0"
        
        adb_manager = ADBManager()
        result = adb_manager.connect_device("192.168.1.100", 5555)
        
        self.assertTrue(result)
        mock_client.return_value.remote_connect.assert_called_with("192.168.1.100", 5555)
    
    @patch('models.adbmanager.AdbClient')
    def test_connect_device_failure(self, mock_client):
        """Test failed device connection"""
        mock_client.return_value.remote_connect.side_effect = Exception("Connection failed")
        mock_client.return_value.version.return_value = "1.0.0"
        
        adb_manager = ADBManager()
        result = adb_manager.connect_device("invalid_ip", 5555)
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
