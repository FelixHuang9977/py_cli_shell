import argparse
import subprocess
import smbus
from typing import List, Dict, Optional
import time

class I2CDevice:
    def __init__(self, bus_num: int, address: int, name: Optional[str] = None):
        self.bus_num = bus_num
        self.address = address
        self.name = name or f"Unknown device at 0x{address:02X}"

def get_i2c_buses() -> List[int]:
    """獲取系統中可用的 I2C 總線"""
    try:
        result = subprocess.run(['i2cdetect', '-l'], 
                              capture_output=True, 
                              text=True)
        if result.returncode != 0:
            raise Exception(f"i2cdetect command failed: {result.stderr}")
        
        buses = []
        for line in result.stdout.splitlines():
            if line.startswith('i2c-'):
                bus_num = int(line.split('-')[1].split()[0])
                buses.append(bus_num)
        return sorted(buses)
    except FileNotFoundError:
        print("Error: 'i2cdetect' command not found. Please install i2c-tools.")
        return []
    except Exception as e:
        print(f"Error getting I2C buses: {str(e)}")
        return []

def scan_i2c_bus(bus_num: int) -> List[I2CDevice]:
    """掃描指定 I2C 總線上的所有設備"""
    devices = []
    try:
        bus = smbus.SMBus(bus_num)
        for addr in range(0x03, 0x77):  # 標準 I2C 地址範圍
            try:
                bus.read_byte(addr)
                devices.append(I2CDevice(bus_num, addr))
            except OSError:  # 設備不存在
                continue
            except Exception as e:
                print(f"Error accessing address 0x{addr:02X}: {str(e)}")
        bus.close()
    except Exception as e:
        print(f"Error scanning bus {bus_num}: {str(e)}")
    return devices

def read_i2c_device(bus_num: int, address: int, register: int, 
                   length: int = 1) -> List[int]:
    """從 I2C 設備讀取數據"""
    try:
        bus = smbus.SMBus(bus_num)
        data = []
        for i in range(length):
            value = bus.read_byte_data(address, register + i)
            data.append(value)
        bus.close()
        return data
    except Exception as e:
        print(f"Error reading from device: {str(e)}")
        return []

def write_i2c_device(bus_num: int, address: int, register: int, 
                    values: List[int]) -> bool:
    """向 I2C 設備寫入數據"""
    try:
        bus = smbus.SMBus(bus_num)
        for i, value in enumerate(values):
            bus.write_byte_data(address, register + i, value)
        bus.close()
        return True
    except Exception as e:
        print(f"Error writing to device: {str(e)}")
        return False

def setup_parser():
    parser = argparse.ArgumentParser(
        description='I2C device management tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List I2C buses')
    
    # scan command
    scan_parser = subparsers.add_parser('scan', help='Scan I2C bus for devices')
    scan_parser.add_argument('-b', '--bus', type=int, 
                            help='Bus number to scan (default: scan all buses)')
    
    # read command
    read_parser = subparsers.add_parser('read', help='Read from I2C device')
    read_parser.add_argument('-b', '--bus', type=int, required=True,
                            help='Bus number')
    read_parser.add_argument('-a', '--address', type=lambda x: int(x, 0), 
                            required=True,
                            help='Device address (e.g., 0x50)')
    read_parser.add_argument('-r', '--register', type=lambda x: int(x, 0), 
                            required=True,
                            help='Register address (e.g., 0x00)')
    read_parser.add_argument('-l', '--length', type=int, default=1,
                            help='Number of bytes to read (default: 1)')
    
    # write command
    write_parser = subparsers.add_parser('write', help='Write to I2C device')
    write_parser.add_argument('-b', '--bus', type=int, required=True,
                             help='Bus number')
    write_parser.add_argument('-a', '--address', type=lambda x: int(x, 0), 
                             required=True,
                             help='Device address (e.g., 0x50)')
    write_parser.add_argument('-r', '--register', type=lambda x: int(x, 0), 
                             required=True,
                             help='Register address (e.g., 0x00)')
    write_parser.add_argument('-d', '--data', type=lambda x: int(x, 0), 
                             nargs='+', required=True,
                             help='Data bytes to write (e.g., 0x12 0x34)')
    
    return parser

def show_usage():
    """顯示使用說明"""
    print("\nUsage:")
    print("  i2c list                    - List all I2C buses")
    print("  i2c scan [-b BUS]           - Scan for devices on specified bus")
    print("  i2c read -b BUS -a ADDR -r REG [-l LEN]")
    print("                              - Read from I2C device")
    print("  i2c write -b BUS -a ADDR -r REG -d DATA...")
    print("                              - Write to I2C device")
    print("\nExamples:")
    print("  i2c list")
    print("  i2c scan -b 1")
    print("  i2c read -b 1 -a 0x50 -r 0x00 -l 4")
    print("  i2c write -b 1 -a 0x50 -r 0x00 -d 0x12 0x34")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            buses = get_i2c_buses()
            if not buses:
                print("No I2C buses found.")
                return 1
            print("\nAvailable I2C buses:")
            for bus in buses:
                print(f"  i2c-{bus}")
                
        elif args.command == 'scan':
            if args.bus is not None:
                buses = [args.bus]
            else:
                buses = get_i2c_buses()
                
            for bus in buses:
                print(f"\nScanning I2C bus {bus}:")
                devices = scan_i2c_bus(bus)
                if devices:
                    print("  Address  Device")
                    print("  -------  ------")
                    for dev in devices:
                        print(f"  0x{dev.address:02X}     {dev.name}")
                else:
                    print("  No devices found")
                    
        elif args.command == 'read':
            data = read_i2c_device(args.bus, args.address, 
                                 args.register, args.length)
            if data:
                print("\nRead data:")
                for i, value in enumerate(data):
                    print(f"  Register 0x{args.register + i:02X}: 0x{value:02X}")
                    
        elif args.command == 'write':
            if write_i2c_device(args.bus, args.address, args.register, args.data):
                print("Write successful")
            else:
                print("Write failed")
                return 1
                
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))