import argparse
import subprocess
import re
from typing import List, Dict, Optional

def get_usb_devices() -> List[Dict]:
    """獲取所有 USB 設備信息"""
    try:
        result = subprocess.run(['lsusb', '-v'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"lsusb command failed: {result.stderr}")
            
        devices = []
        current_device = None
        
        for line in result.stdout.splitlines():
            if line.startswith('Bus '):
                if current_device:
                    devices.append(current_device)
                bus_dev = re.match(r'Bus (\d+) Device (\d+): ID (\w+):(\w+)', line)
                if bus_dev:
                    current_device = {
                        'bus': bus_dev.group(1),
                        'device': bus_dev.group(2),
                        'vendor_id': bus_dev.group(3),
                        'product_id': bus_dev.group(4)
                    }
            elif current_device and ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                if 'iManufacturer' in key:
                    current_device['manufacturer'] = value
                elif 'iProduct' in key:
                    current_device['product'] = value
                elif 'bcdUSB' in key:
                    current_device['usb_version'] = value
                    
        if current_device:
            devices.append(current_device)
            
        return devices
    except FileNotFoundError:
        raise Exception("'lsusb' command not found. Please install usbutils.")
    except Exception as e:
        raise Exception(f"Error listing USB devices: {str(e)}")

def get_device_details(bus: str, device: str) -> Dict:
    """獲取特定 USB 設備的詳細信息"""
    try:
        result = subprocess.run(['lsusb', '-D', f'/dev/bus/usb/{bus}/{device}'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"lsusb detail command failed: {result.stderr}")
            
        details = {'bus': bus, 'device': device}
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                details[key] = value
                
        return details
    except Exception as e:
        raise Exception(f"Error getting device details: {str(e)}")

def setup_parser():
    parser = argparse.ArgumentParser(description='USB device management tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    subparsers.add_parser('list', help='List all USB devices')
    
    # info command
    info_parser = subparsers.add_parser('info', 
                                       help='Show detailed device information')
    info_parser.add_argument('bus', help='Bus number')
    info_parser.add_argument('device', help='Device number')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  usb list             - List all USB devices")
    print("  usb info BUS DEV     - Show detailed device information")
    print("\nExamples:")
    print("  usb list")
    print("  usb info 001 002")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            devices = get_usb_devices()
            if devices:
                print("\nUSB Devices:")
                print(f"{'Bus:Dev':<10} {'VID:PID':<12} "
                      f"{'Manufacturer':<20} {'Product'}")
                print("-" * 80)
                for dev in devices:
                    bus_dev = f"{dev['bus']}:{dev['device']}"
                    vid_pid = f"{dev['vendor_id']}:{dev['product_id']}"
                    mfg = dev.get('manufacturer', 'N/A')
                    prod = dev.get('product', 'N/A')
                    print(f"{bus_dev:<10} {vid_pid:<12} {mfg:<20} {prod}")
                    
        elif args.command == 'info':
            details = get_device_details(args.bus, args.device)
            if details:
                print(f"\nDevice Details (Bus {args.bus}, Device {args.device}):")
                for key, value in details.items():
                    if key not in ['bus', 'device']:
                        print(f"{key}: {value}")
                        
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))