import argparse
import subprocess
import os
from typing import List, Dict, Optional

def read_acpi_tables() -> List[Dict[str, str]]:
    """讀取系統中的 ACPI 表"""
    tables = []
    try:
        # 使用 acpidump 獲取表信息
        result = subprocess.run(['acpidump', '-s'], 
                              capture_output=True, 
                              text=True)
        if result.returncode != 0:
            raise Exception(f"acpidump command failed: {result.stderr}")
            
        current_table = {}
        for line in result.stdout.splitlines():
            if line.startswith('ACPI table ['):
                if current_table:
                    tables.append(current_table)
                current_table = {'name': line.split('[')[1].split(']')[0]}
            elif ':' in line:
                key, value = [x.strip() for x in line.split(':', 1)]
                current_table[key] = value
                
        if current_table:
            tables.append(current_table)
            
        return tables
    except FileNotFoundError:
        print("Error: 'acpidump' command not found. Please install acpica-tools.")
        return []
    except Exception as e:
        print(f"Error reading ACPI tables: {str(e)}")
        return []

def read_acpi_table_content(table_name: str) -> Optional[str]:
    """讀取特定 ACPI 表的內容"""
    try:
        # 使用 acpidump 獲取特定表的內容
        result = subprocess.run(['acpidump', '-b', '-t', table_name], 
                              capture_output=True)
        if result.returncode != 0:
            raise Exception(f"acpidump command failed: {result.stderr}")
            
        # 使用 iasl 反編譯表內容
        with open(f'{table_name}.dat', 'wb') as f:
            f.write(result.stdout)
            
        decompile = subprocess.run(['iasl', '-d', f'{table_name}.dat'],
                                 capture_output=True,
                                 text=True)
                                 
        # 讀取反編譯結果
        if os.path.exists(f'{table_name}.dsl'):
            with open(f'{table_name}.dsl', 'r') as f:
                content = f.read()
                
            # 清理臨時文件
            os.remove(f'{table_name}.dat')
            os.remove(f'{table_name}.dsl')
            
            return content
    except Exception as e:
        print(f"Error reading table {table_name}: {str(e)}")
    return None

def setup_parser():
    parser = argparse.ArgumentParser(
        description='ACPI table management tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    list_parser = subparsers.add_parser('list', 
                                       help='List all ACPI tables')
    
    # show command
    show_parser = subparsers.add_parser('show', 
                                       help='Show specific ACPI table content')
    show_parser.add_argument('table', help='Table name (e.g., DSDT, SSDT)')
    
    return parser

def show_usage():
    """顯示使用說明"""
    print("\nUsage:")
    print("  acpi list              - List all ACPI tables")
    print("  acpi show TABLE        - Show specific table content")
    print("\nExamples:")
    print("  acpi list")
    print("  acpi show DSDT")
    print("  acpi show SSDT")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            tables = read_acpi_tables()
            if not tables:
                print("No ACPI tables found.")
                return 1
                
            print("\nACPI Tables:")
            print(f"{'Table':<8} {'Length':<10} {'OEM ID':<8} {'OEM Table ID':<16}")
            print("-" * 50)
            
            for table in tables:
                name = table.get('name', 'Unknown')
                length = table.get('Table Length', 'Unknown')
                oem_id = table.get('OEM ID', 'Unknown')
                oem_table_id = table.get('OEM Table ID', 'Unknown')
                print(f"{name:<8} {length:<10} {oem_id:<8} {oem_table_id:<16}")
                
        elif args.command == 'show':
            content = read_acpi_table_content(args.table)
            if content:
                print(f"\nContent of {args.table}:")
                print(content)
            else:
                print(f"Could not read table {args.table}")
                return 1
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))