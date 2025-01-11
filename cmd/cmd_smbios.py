import argparse
import subprocess
import json
from typing import List, Dict, Optional

def get_smbios_info() -> Dict[str, List[Dict]]:
    """獲取 SMBIOS 信息"""
    try:
        # 使用 dmidecode 獲取所有信息
        result = subprocess.run(['dmidecode', '-j'], 
                              capture_output=True, 
                              text=True)
        if result.returncode != 0:
            raise Exception(f"dmidecode command failed: {result.stderr}")
            
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("Error: 'dmidecode' command not found. Please install dmidecode.")
        return {}
    except json.JSONDecodeError:
        print("Error: Could not parse dmidecode output.")
        return {}
    except Exception as e:
        print(f"Error getting SMBIOS info: {str(e)}")
        return {}

def get_type_info(type_id: int) -> List[Dict]:
    """獲取特定類型的 SMBIOS 信息"""
    try:
        result = subprocess.run(['dmidecode', '-t', str(type_id)], 
                              capture_output=True, 
                              text=True)
        if result.returncode != 0:
            raise Exception(f"dmidecode command failed: {result.stderr}")
            
        return parse_dmidecode_output(result.stdout)
    except Exception as e:
        print(f"Error getting type {type_id} info: {str(e)}")
        return []

def parse_dmidecode_output(output: str) -> List[Dict]:
    """解析 dmidecode 輸出"""
    entries = []
    current_entry = {}
    current_section = None
    
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('Handle '):
            if current_entry:
                entries.append(current_entry)
            current_entry = {'Handle': line.split('Handle')[1].strip()}
            current_section = None
        elif line.startswith('\t\t'):
            if current_section:
                if isinstance(current_entry[current_section], list):
                    current_entry[current_section].append(line.strip())
                else:
                    current_entry[current_section] = [
                        current_entry[current_section], 
                        line.strip()
                    ]
        elif line.startswith('\t'):
            if ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                current_entry[key] = value
                current_section = key
            else:
                current_section = line.strip()
                current_entry[current_section] = []
                
    if current_entry:
        entries.append(current_entry)
        
    return entries

def setup_parser():
    parser = argparse.ArgumentParser(
        description='SMBIOS information tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    list_parser = subparsers.add_parser('list', 
                                       help='List all SMBIOS information')
    
    # type command
    type_parser = subparsers.add_parser('type', 
                                       help='Show specific type information')
    type_parser.add_argument('type_id', type=int, 
                            help='SMBIOS type ID (0-42)')
    
    return parser

def show_usage():
    """顯示使用說明"""
    print("\nUsage:")
    print("  smbios list            - List all SMBIOS information")
    print("  smbios type TYPE_ID    - Show specific type information")
    print("\nCommon type IDs:")
    print("  0  - BIOS")
    print("  1  - System")
    print("  2  - Baseboard")
    print("  3  - Chassis")
    print("  4  - Processor")
    print("  17 - Memory Device")
    print("\nExamples:")
    print("  smbios list")
    print("  smbios type 0")
    print("  smbios type 4")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            info = get_smbios_info()
            if not info:
                print("No SMBIOS information available.")
                return 1
                
            print("\nSMBIOS Information:")
            for type_name, entries in info.items():
                print(f"\n{type_name}:")
                for entry in entries:
                    for key, value in entry.items():
                        if isinstance(value, list):
                            print(f"  {key}:")
                            for item in value:
                                print(f"    {item}")
                        else:
                            print(f"  {key}: {value}")
                            
        elif args.command == 'type':
            entries = get_type_info(args.type_id)
            if not entries:
                print(f"No information available for type {args.type_id}")
                return 1
                
            print(f"\nType {args.type_id} Information:")
            for entry in entries:
                for key, value in entry.items():
                    if isinstance(value, list):
                        print(f"\n{key}:")
                        for item in value:
                            print(f"  {item}")
                    else:
                        print(f"{key}: {value}")
                print()
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))