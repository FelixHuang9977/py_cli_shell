from testcase.base_test import BaseTest
import subprocess
import re

class TestUSBInfo(BaseTest):
    """USB related test cases"""
    
    def setup_method(self):
        """Setup method that runs before each test"""
        # 確保有必要的命令可用
        self.check_command_exists('lsusb')
    
    def check_command_exists(self, command):
        """檢查系統是否有需要的命令"""
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Command '{command}' not found. Please install required packages.")

    def test_usb_devices_present(self):
        """測試是否能檢測到 USB 設備"""
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        assert result.returncode == 0, "Failed to run lsusb command"
        assert len(result.stdout.strip().split('\n')) > 0, "No USB devices detected"

    def test_usb_device_info(self):
        """測試 USB 設備詳細信息"""
        result = subprocess.run(['lsusb', '-v'], capture_output=True, text=True)
        assert result.returncode == 0, "Failed to get detailed USB information"
        
        # 檢查輸出中是否包含關鍵的 USB 信息字段
        output = result.stdout
        assert 'Device Descriptor:' in output, "No USB device descriptor found"
        assert 'Configuration Descriptor:' in output, "No USB configuration descriptor found"

    def test_specific_usb_device(self):
        """測試特定 USB 設備的存在和狀態"""
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        devices = result.stdout.strip().split('\n')
        
        # 解析設備信息
        device_info = []
        for device in devices:
            if device:
                match = re.match(r'Bus (\d{3}) Device (\d{3}): ID (\w{4}):(\w{4})', device)
                if match:
                    device_info.append({
                        'bus': match.group(1),
                        'device': match.group(2),
                        'vendor_id': match.group(3),
                        'product_id': match.group(4)
                    })
        
        assert len(device_info) > 0, "No USB devices could be parsed"

    def test_usb_ports_status(self):
        """測試 USB 端口狀態"""
        try:
            with open('/sys/kernel/debug/usb/devices', 'r') as f:
                content = f.read()
                assert 'T:' in content, "No USB topology information found"
                assert 'B:' in content, "No USB bandwidth information found"
        except FileNotFoundError:
            # 如果無法直接讀取設備文件，嘗試使用 lsusb
            result = subprocess.run(['lsusb', '-t'], capture_output=True, text=True)
            assert result.returncode == 0, "Failed to get USB port status"
            assert len(result.stdout.strip()) > 0, "No USB port information available"

    def test_usb_bandwidth(self):
        """測試 USB 頻寬使用情況"""
        try:
            # 嘗試讀取 USB 控制器的頻寬信息
            result = subprocess.run(['cat', '/sys/kernel/debug/usb/devices'], 
                                 capture_output=True, text=True)
            
            if result.returncode == 0:
                content = result.stdout
                # 檢查是否包含速度相關信息
                assert any(speed in content for speed in ['480', '12', '1.5']), \
                    "No USB speed information found"
            else:
                self.skip_test("Unable to access USB bandwidth information")
        except Exception:
            self.skip_test("USB bandwidth test not supported on this system")

    def skip_test(self, message):
        """Skip the current test with a message"""
        import pytest
        pytest.skip(message)