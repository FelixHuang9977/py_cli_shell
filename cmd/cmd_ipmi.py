import argparse
import subprocess
from typing import List, Dict, Optional

def run_ipmi_command(command: List[str]) -> str:
    """執行 IPMI 命令"""
    try:
        cmd = ['ipmitool'] + command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"IPMI command failed: {result.stderr}")
        return result.stdout
    except FileNotFoundError:
        raise Exception("'ipmitool' not found. Please install ipmitool.")
    except Exception as e:
        raise Exception(f"IPMI command error: {str(e)}")

def get_sensor_data() -> List[Dict[str, str]]:
    """獲取所有感測器數據"""
    sensors = []
    try:
        output = run_ipmi_command(['sensor', 'list'])
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split('|')
            if len(parts) >= 4:
                sensors.append({
                    'name': parts[0].strip(),
                    'value': parts[1].strip(),
                    'unit': parts[2].strip(),
                    'status': parts[3].strip()
                })
        return sensors
    except Exception as e:
        print(f"Error getting sensor data: {str(e)}")
        return []

def get_fru_info() -> Dict[str, Dict[str, str]]:
    """獲取 FRU 信息"""
    try:
        output = run_ipmi_command(['fru', 'print'])
        fru_info = {}
        current_section = None
        
        for line in output.splitlines():
            if not line.strip():
                continue
            if not line.startswith(' '):
                current_section = line.strip(':')
                fru_info[current_section] = {}
            elif current_section and ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                fru_info[current_section][key] = value
                
        return fru_info
    except Exception as e:
        print(f"Error getting FRU info: {str(e)}")
        return {}

def get_sel_entries(count: int = 10) -> List[Dict[str, str]]:
    """獲取系統事件日誌"""
    try:
        output = run_ipmi_command(['sel', 'list', 'last', str(count)])
        entries = []
        for line in output.splitlines():
            if '|' in line:
                parts = line.split('|')
                entries.append({
                    'id': parts[0].strip(),
                    'timestamp': parts[1].strip(),
                    'event': parts[2].strip() if len(parts) > 2 else 'Unknown'
                })
        return entries
    except Exception as e:
        print(f"Error getting SEL entries: {str(e)}")
        return []

def setup_parser():
    parser = argparse.ArgumentParser(description='IPMI management tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # sensor command
    subparsers.add_parser('sensor', help='Show sensor readings')
    
    # fru command
    subparsers.add_parser('fru', help='Show FRU information')
    
    # sel command
    sel_parser = subparsers.add_parser('sel', help='Show system event log')
    sel_parser.add_argument('-n', '--count', type=int, default=10,
                           help='Number of entries to show (default: 10)')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  ipmi sensor           - Show all sensor readings")
    print("  ipmi fru              - Show FRU information")
    print("  ipmi sel [-n COUNT]   - Show system event log")
    print("\nExamples:")
    print("  ipmi sensor")
    print("  ipmi fru")
    print("  ipmi sel -n 20")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'sensor':
            sensors = get_sensor_data()
            if sensors:
                print("\nSensor Readings:")
                print(f"{'Name':<20} {'Value':<10} {'Unit':<10} {'Status':<10}")
                print("-" * 60)
                for sensor in sensors:
                    print(f"{sensor['name']:<20} "
                          f"{sensor['value']:<10} "
                          f"{sensor['unit']:<10} "
                          f"{sensor['status']:<10}")
                          
        elif args.command == 'fru':
            fru_info = get_fru_info()
            if fru_info:
                print("\nFRU Information:")
                for section, data in fru_info.items():
                    print(f"\n{section}:")
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                        
        elif args.command == 'sel':
            entries = get_sel_entries(args.count)
            if entries:
                print("\nSystem Event Log:")
                print(f"{'ID':<6} {'Timestamp':<20} {'Event'}")
                print("-" * 60)
                for entry in entries:
                    print(f"{entry['id']:<6} "
                          f"{entry['timestamp']:<20} "
                          f"{entry['event']}")
                          
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))