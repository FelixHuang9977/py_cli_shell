import argparse
import subprocess
import re
from typing import List, Dict, Optional

class PCIDevice:
    def __init__(self, bus: str, device_type: str, vendor: str, model: str):
        self.bus = bus
        self.device_type = device_type
        self.vendor = vendor
        self.model = model

def get_pci_devices() -> List[PCIDevice]:
    """獲取系統中的所有 PCI 設備"""
    try:
        # 執行 lspci -vmm 獲取詳細信息
        result = subprocess.run(['lspci', '-vmm'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            raise Exception(f"lspci command failed: {result.stderr}")

        devices = []
        current_device = {}
        
        # 解析輸出
        for line in result.stdout.splitlines():
            if not line.strip():
                if current_device:
                    devices.append(PCIDevice(
                        bus=current_device.get('Slot', 'Unknown'),
                        device_type=current_device.get('Class', 'Unknown'),
                        vendor=current_device.get('Vendor', 'Unknown'),
                        model=current_device.get('Device', 'Unknown')
                    ))
                    current_device = {}
                continue
                
            if ':' in line:
                key, value = line.split(':', 1)
                current_device[key.strip()] = value.strip()
        
        # 處理最後一個設備
        if current_device:
            devices.append(PCIDevice(
                bus=current_device.get('Slot', 'Unknown'),
                device_type=current_device.get('Class', 'Unknown'),
                vendor=current_device.get('Vendor', 'Unknown'),
                model=current_device.get('Device', 'Unknown')
            ))
            
        return devices
        
    except FileNotFoundError:
        print("Error: 'lspci' command not found. Please install pciutils.")
        return []
    except Exception as e:
        print(f"Error getting PCI devices: {str(e)}")
        return []

def format_device_info(device: PCIDevice, verbose: bool = False) -> str:
    """格式化設備信息輸出"""
    if verbose:
        return (f"Bus: {device.bus}\n"
                f"Type: {device.device_type}\n"
                f"Vendor: {device.vendor}\n"
                f"Model: {device.model}\n")
    else:
        return f"{device.bus:<10} {device.device_type:<20} {device.vendor:<20} {device.model}"

def setup_parser():
    parser = argparse.ArgumentParser(
        description='List PCI devices in the system'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information'
    )
    parser.add_argument(
        '-t', '--type',
        help='Filter by device type (e.g., "VGA", "Network", "Storage")'
    )
    parser.add_argument(
        '-b', '--bus',
        help='Filter by bus address'
    )
    return parser

def execute(args):
    try:
        devices = get_pci_devices()
        
        if not devices:
            print("No PCI devices found.")
            return 1
            
        # 應用過濾器
        if args.type:
            devices = [d for d in devices if args.type.lower() in d.device_type.lower()]
        if args.bus:
            devices = [d for d in devices if args.bus.lower() in d.bus.lower()]
            
        if not devices:
            print("No devices match the specified criteria.")
            return 1
            
        # 輸出表頭
        if not args.verbose:
            print(f"{'Bus':<10} {'Type':<20} {'Vendor':<20} {'Model'}")
            print("-" * 70)
            
        # 輸出設備信息
        for device in devices:
            print(format_device_info(device, args.verbose))
            if args.verbose:
                print()  # 在詳細模式下添加空行
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))