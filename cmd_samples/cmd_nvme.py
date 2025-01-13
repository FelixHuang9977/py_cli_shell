import argparse
import subprocess
import json
from typing import List, Dict, Optional

def get_nvme_list() -> List[Dict]:
    """獲取所有 NVMe 設備列表"""
    try:
        result = subprocess.run(['nvme', 'list', '-o', 'json'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"nvme list command failed: {result.stderr}")
            
        data = json.loads(result.stdout)
        return data.get('Devices', [])
    except FileNotFoundError:
        raise Exception("'nvme' command not found. Please install nvme-cli.")
    except Exception as e:
        raise Exception(f"Error listing NVMe devices: {str(e)}")

def get_smart_info(device: str) -> Dict:
    """獲取 NVMe 設備的 SMART 信息"""
    try:
        result = subprocess.run(['nvme', 'smart-log', device],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"nvme smart-log command failed: {result.stderr}")
            
        smart_info = {}
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                smart_info[key] = value
                
        return smart_info
    except Exception as e:
        raise Exception(f"Error getting SMART info for {device}: {str(e)}")

def get_error_log(device: str) -> List[Dict]:
    """獲取 NVMe 設備的錯誤日誌"""
    try:
        result = subprocess.run(['nvme', 'error-log', device],
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"nvme error-log command failed: {result.stderr}")
            
        errors = []
        current_error = {}
        for line in result.stdout.splitlines():
            if line.startswith('Error'):
                if current_error:
                    errors.append(current_error)
                current_error = {'id': line.split()[1]}
            elif ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                current_error[key] = value
                
        if current_error:
            errors.append(current_error)
            
        return errors
    except Exception as e:
        raise Exception(f"Error getting error log for {device}: {str(e)}")

def setup_parser():
    parser = argparse.ArgumentParser(description='NVMe device management tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    subparsers.add_parser('list', help='List all NVMe devices')
    
    # smart command
    smart_parser = subparsers.add_parser('smart', 
                                        help='Show SMART information')
    smart_parser.add_argument('device', help='Device path (e.g., /dev/nvme0)')
    
    # error command
    error_parser = subparsers.add_parser('error', 
                                        help='Show error log')
    error_parser.add_argument('device', help='Device path (e.g., /dev/nvme0)')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  nvme list            - List all NVMe devices")
    print("  nvme smart DEVICE    - Show SMART information")
    print("  nvme error DEVICE    - Show error log")
    print("\nExamples:")
    print("  nvme list")
    print("  nvme smart /dev/nvme0")
    print("  nvme error /dev/nvme0")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            devices = get_nvme_list()
            if devices:
                print("\nNVMe Devices:")
                print(f"{'Device':<15} {'Model':<30} {'Capacity':<15} {'Serial'}")
                print("-" * 80)
                for dev in devices:
                    print(f"{dev['DevicePath']:<15} "
                          f"{dev.get('ModelNumber', 'N/A'):<30} "
                          f"{dev.get('PhysicalSize', 'N/A'):<15} "
                          f"{dev.get('SerialNumber', 'N/A')}")
                          
        elif args.command == 'smart':
            info = get_smart_info(args.device)
            if info:
                print(f"\nSMART Information for {args.device}:")
                for key, value in info.items():
                    print(f"{key}: {value}")
                    
        elif args.command == 'error':
            errors = get_error_log(args.device)
            if errors:
                print(f"\nError Log for {args.device}:")
                for error in errors:
                    print(f"\nError {error['id']}:")
                    for key, value in error.items():
                        if key != 'id':
                            print(f"  {key}: {value}")
            else:
                print("No errors found")
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))