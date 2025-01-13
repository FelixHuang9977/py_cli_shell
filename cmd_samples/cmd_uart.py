import argparse
import subprocess
import glob
import serial
import serial.tools.list_ports
import time
import os
from typing import List, Dict, Optional, Tuple

class UARTDevice:
    def __init__(self, port: str):
        self.port = port
        self.info = self._get_device_info()
        
    def _get_device_info(self) -> Dict[str, str]:
        """獲取設備詳細信息"""
        info = {'port': self.port}
        try:
            port_info = next((p for p in serial.tools.list_ports.comports() 
                            if p.device == self.port), None)
            if port_info:
                info.update({
                    'name': port_info.name,
                    'description': port_info.description,
                    'hardware_id': port_info.hwid,
                    'vid': hex(port_info.vid) if port_info.vid else 'N/A',
                    'pid': hex(port_info.pid) if port_info.pid else 'N/A',
                    'serial_number': port_info.serial_number or 'N/A',
                    'manufacturer': port_info.manufacturer or 'N/A',
                    'location': port_info.location or 'N/A'
                })
        except Exception as e:
            print(f"Warning: Could not get detailed info for {self.port}: {e}")
        return info

def get_uart_devices() -> List[UARTDevice]:
    """獲取系統中的所有 UART 設備"""
    devices = []
    
    # 使用 serial.tools.list_ports 獲取所有串口設備
    for port in serial.tools.list_ports.comports():
        devices.append(UARTDevice(port.device))
        
    # 額外檢查傳統串口設備
    traditional_ports = (glob.glob('/dev/ttyS*') + 
                        glob.glob('/dev/ttyUSB*') + 
                        glob.glob('/dev/ttyACM*') + 
                        glob.glob('/dev/ttyAMA*'))
    
    # 添加尚未包含的設備
    existing_ports = {dev.port for dev in devices}
    for port in traditional_ports:
        if port not in existing_ports:
            devices.append(UARTDevice(port))
            
    return devices

def test_uart_connection(device: str, baudrate: int, 
                        timeout: float = 1.0) -> Tuple[bool, str]:
    """測試 UART 連接"""
    try:
        with serial.Serial(device, baudrate, timeout=timeout) as ser:
            # 清空緩衝區
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            # 寫入測試數據
            test_data = b'UART TEST\n'
            ser.write(test_data)
            ser.flush()
            
            # 嘗試讀取回顯
            response = ser.readline()
            
            if response:
                return True, f"Received response: {response.decode('ascii', 'ignore').strip()}"
            return True, "Connection successful (no response)"
    except Exception as e:
        return False, str(e)

def monitor_uart(device: str, baudrate: int, duration: int = 10) -> List[str]:
    """監控 UART 數據"""
    messages = []
    try:
        with serial.Serial(device, baudrate, timeout=0.1) as ser:
            start_time = time.time()
            while time.time() - start_time < duration:
                if ser.in_waiting:
                    line = ser.readline()
                    try:
                        decoded = line.decode('ascii', 'ignore').strip()
                        if decoded:
                            messages.append(decoded)
                    except Exception as e:
                        messages.append(f"Error decoding: {line}")
    except Exception as e:
        messages.append(f"Error: {str(e)}")
    return messages

def send_uart_data(device: str, baudrate: int, data: str, 
                   as_hex: bool = False) -> Tuple[bool, str]:
    """發送數據到 UART 設備"""
    try:
        with serial.Serial(device, baudrate) as ser:
            if as_hex:
                # 將十六進制字符串轉換為位元組
                try:
                    data = bytes.fromhex(data.replace('0x', ''))
                except ValueError:
                    return False, "Invalid hex data format"
            else:
                data = data.encode('ascii')
                
            ser.write(data)
            ser.flush()
            return True, f"Sent {len(data)} bytes successfully"
    except Exception as e:
        return False, str(e)

def configure_uart(device: str, baudrate: int, bytesize: int = 8,
                  parity: str = 'N', stopbits: float = 1) -> Tuple[bool, str]:
    """配置 UART 設備參數"""
    try:
        with serial.Serial(device, baudrate,
                          bytesize=bytesize,
                          parity=parity,
                          stopbits=stopbits) as ser:
            config = {
                'baudrate': ser.baudrate,
                'bytesize': ser.bytesize,
                'parity': ser.parity,
                'stopbits': ser.stopbits,
                'xonxoff': ser.xonxoff,
                'rtscts': ser.rtscts,
                'dsrdtr': ser.dsrdtr
            }
            return True, f"Configuration successful: {config}"
    except Exception as e:
        return False, str(e)

def setup_parser():
    parser = argparse.ArgumentParser(description='UART device management tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list command
    list_parser = subparsers.add_parser('list', 
                                       help='List all UART devices')
    list_parser.add_argument('-v', '--verbose', action='store_true',
                            help='Show detailed device information')
    
    # test command
    test_parser = subparsers.add_parser('test', 
                                       help='Test UART connection')
    test_parser.add_argument('device', help='Device path (e.g., /dev/ttyUSB0)')
    test_parser.add_argument('-b', '--baudrate', type=int, default=115200,
                            help='Baudrate (default: 115200)')
    
    # monitor command
    monitor_parser = subparsers.add_parser('monitor', 
                                          help='Monitor UART data')
    monitor_parser.add_argument('device', help='Device path')
    monitor_parser.add_argument('-b', '--baudrate', type=int, default=115200,
                              help='Baudrate (default: 115200)')
    monitor_parser.add_argument('-t', '--time', type=int, default=10,
                              help='Monitoring duration in seconds (default: 10)')
    
    # send command
    send_parser = subparsers.add_parser('send', 
                                       help='Send data to UART device')
    send_parser.add_argument('device', help='Device path')
    send_parser.add_argument('data', help='Data to send')
    send_parser.add_argument('-b', '--baudrate', type=int, default=115200,
                            help='Baudrate (default: 115200)')
    send_parser.add_argument('-x', '--hex', action='store_true',
                            help='Send data as hex')
    
    # config command
    config_parser = subparsers.add_parser('config', 
                                         help='Configure UART device')
    config_parser.add_argument('device', help='Device path')
    config_parser.add_argument('-b', '--baudrate', type=int, default=115200,
                              help='Baudrate (default: 115200)')
    config_parser.add_argument('--bytesize', type=int, choices=[5,6,7,8], 
                              default=8,
                              help='Byte size (default: 8)')
    config_parser.add_argument('--parity', choices=['N','E','O','M','S'], 
                              default='N',
                              help='Parity (default: N)')
    config_parser.add_argument('--stopbits', type=float, choices=[1,1.5,2], 
                              default=1,
                              help='Stop bits (default: 1)')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  uart list [-v]       - List all UART devices")
    print("  uart test DEVICE [-b BAUDRATE]")
    print("                      - Test UART connection")
    print("  uart monitor DEVICE [-b BAUDRATE] [-t TIME]")
    print("                      - Monitor UART data")
    print("  uart send DEVICE DATA [-b BAUDRATE] [-x]")
    print("                      - Send data to UART device")
    print("  uart config DEVICE [-b BAUDRATE] [--bytesize BYTES]")
    print("                    [--parity PARITY] [--stopbits BITS]")
    print("                      - Configure UART device")
    print("\nExamples:")
    print("  uart list -v")
    print("  uart test /dev/ttyUSB0 -b 9600")
    print("  uart monitor /dev/ttyUSB0 -t 30")
    print("  uart send /dev/ttyUSB0 'Hello' -b 115200")
    print("  uart send /dev/ttyUSB0 '48656C6C6F' -x")
    print("  uart config /dev/ttyUSB0 -b 9600 --parity E")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'list':
            devices = get_uart_devices()
            if not devices:
                print("No UART devices found.")
                return 1
                
            print("\nUART Devices:")
            if args.verbose:
                for dev in devices:
                    print(f"\nDevice: {dev.port}")
                    for key, value in dev.info.items():
                        if key != 'port':
                            print(f"  {key}: {value}")
            else:
                print(f"{'Device':<15} {'Description':<30} {'Manufacturer'}")
                print("-" * 70)
                for dev in devices:
                    print(f"{dev.info['port']:<15} "
                          f"{dev.info.get('description', 'N/A'):<30} "
                          f"{dev.info.get('manufacturer', 'N/A')}")
                
        elif args.command == 'test':
            print(f"\nTesting connection to {args.device} "
                  f"at {args.baudrate} baud...")
            success, message = test_uart_connection(args.device, args.baudrate)
            print(message)
            return 0 if success else 1
            
        elif args.command == 'monitor':
            print(f"\nMonitoring {args.device} for {args.time} seconds...")
            messages = monitor_uart(args.device, args.baudrate, args.time)
            if messages:
                print("\nReceived data:")
                for msg in messages:
                    print(msg)
            else:
                print("No data received")
                
        elif args.command == 'send':
            success, message = send_uart_data(args.device, args.baudrate, 
                                            args.data, args.hex)
            print(message)
            return 0 if success else 1
            
        elif args.command == 'config':
            success, message = configure_uart(
                args.device, args.baudrate,
                args.bytesize, args.parity, args.stopbits
            )
            print(message)
            return 0 if success else 1
            
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))
