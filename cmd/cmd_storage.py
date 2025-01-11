import argparse
import subprocess
import json
from typing import List, Dict, Optional

def get_block_devices() -> List[Dict]:
    """獲取所有塊設備信息"""
    try:
        result = subprocess.run(['lsblk', '-J', '-o', 
                               'NAME,SIZE,TYPE,MOUNTPOINT,MODEL,SERIAL'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"lsblk command failed: {result.stderr}")
            
        data = json.loads(result.stdout)
        return data.get('blockdevices', [])
    except Exception as e:
        print(f"Error getting block devices: {str(e)}")
        return []

def get_smart_info(device: str) -> Dict:
    """獲取設備的 SMART 信息"""
    try:
        result = subprocess.run(['smartctl', '-a', f'/dev/{device}'],
                              capture_output=True, text=True)
        info = {'device': device, 'smart_enabled': False, 'attributes': []}
        
        for line in result.stdout.splitlines():
            if 'SMART overall-health self-assessment' in line:
                info['health'] = line.split(':')[1].strip()
            elif 'SMART support is:' in line:
                info['smart_enabled'] = 'Enabled' in line
            elif '=' in line and 'Temperature' in line:
                info['temperature'] = line.split('=')[1].strip()
                
        return info
    except Exception as e:
        print(f"Error getting SMART info for {device}: {str(e)}")
        return {}

def get_raid_info() -> Dict:
    """獲取 RAID 信息"""
    try:
        result = subprocess.run(['mdadm', '--detail', '--scan'],
                              capture_output=True, text=True)
        raids = {}
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith('ARRAY'):
                    parts = line.split()
                    device = parts[1]
                    raids[device] = {'status': 'active'}
                    
        return raids
    except Exception as e:
        print(f"Error getting RAID info: {str(e)}")
        return {}

def setup_parser():
    parser = argparse.ArgumentParser(description='Storage information tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    subparsers.add_parser('list', help='List all storage devices')
    
    # smart command
    smart_parser = subparsers.add_parser('smart', 
                                        help='Show SMART information')
    smart_parser.add_argument('device', help='Device name (e.g., sda)')
    
    # raid command
    subparsers.add_parser('raid', help='Show RAID information')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  storage list          - List all storage devices")
    print("  storage smart DEVICE  - Show SMART information for device")
    print("  storage raid          - Show RAID information")
    print("\nExamples:")
    print("  storage list")
    print("  storage smart sda")
    print("  storage raid")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            devices = get_block_devices()
            if devices:
                print("\nStorage Devices:")
                print(f"{'Name':<10} {'Size':<10} {'Type':<10} "
                      f"{'Model':<20} {'Mountpoint'}")
                print("-" * 70)
                for dev in devices:
                    print(f"{dev['name']:<10} "
                          f"{dev['size']:<10} "
                          f"{dev['type']:<10} "
                          f"{dev.get('model', 'N/A'):<20} "
                          f"{dev.get('mountpoint', 'N/A')}")
                          
        elif args.command == 'smart':
            info = get_smart_info(args.device)
            if info:
                print(f"\nSMART Information for /dev/{args.device}:")
                print(f"SMART Status: {'Enabled' if info['smart_enabled'] else 'Disabled'}")
                if 'health' in info:
                    print(f"Health: {info['health']}")
                if 'temperature' in info:
                    print(f"Temperature: {info['temperature']}")
                    
        elif args.command == 'raid':
            raids = get_raid_info()
            if raids:
                print("\nRAID Arrays:")
                for device, info in raids.items():
                    print(f"\nArray: {device}")
                    print(f"Status: {info['status']}")
            else:
                print("No RAID arrays found")
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))