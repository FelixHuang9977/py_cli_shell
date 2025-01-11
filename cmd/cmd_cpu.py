import argparse
import subprocess
import re
import os
import json
from typing import Dict, List, Optional
from pathlib import Path

class CPUInfo:
    def __init__(self):
        self.info = self._get_cpu_info()
        self.topology = self._get_cpu_topology()
        
    def _get_cpu_info(self) -> Dict[str, str]:
        """獲取 CPU 基本信息"""
        info = {}
        try:
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                
            # 基本信息
            model = re.search(r'model name\s+: (.*)', content)
            info['model'] = model.group(1) if model else 'Unknown'
            
            vendor = re.search(r'vendor_id\s+: (.*)', content)
            info['vendor'] = vendor.group(1) if vendor else 'Unknown'
            
            # CPU 頻率
            freq = re.search(r'cpu MHz\s+: ([\d.]+)', content)
            info['current_freq'] = f"{freq.group(1)} MHz" if freq else 'Unknown'
            
            # 快取大小
            cache = re.search(r'cache size\s+: (\d+)', content)
            info['cache'] = f"{cache.group(1)} KB" if cache else 'Unknown'
            
            # CPU Flags
            flags = re.search(r'flags\s+: (.*)', content)
            info['flags'] = flags.group(1).split() if flags else []
            
            # 獲取最大頻率
            max_freq_path = '/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq'
            if os.path.exists(max_freq_path):
                with open(max_freq_path, 'r') as f:
                    max_freq = int(f.read().strip()) / 1000
                    info['max_freq'] = f"{max_freq} MHz"
            return info
        except Exception as e:
            print(f"Error reading CPU info: {str(e)}")
        return {}

    def _get_cpu_topology(self) -> Dict[str, Dict]:
        """獲取 CPU 拓撲信息"""
        topology = {}
        try:
            cpu_path = Path('/sys/devices/system/cpu')
            for cpu_dir in cpu_path.glob('cpu[0-9]*'):
                cpu_num = int(cpu_dir.name[3:])
                topology[cpu_num] = {
                    'online': self._read_sysfs(cpu_dir / 'online', '1') == '1',
                    'core_id': self._read_sysfs(cpu_dir / 'topology/core_id', 'Unknown'),
                    'physical_package_id': self._read_sysfs(cpu_dir / 'topology/physical_package_id', 'Unknown'),
                    'thread_siblings': self._read_sysfs(cpu_dir / 'topology/thread_siblings_list', 'Unknown')
                }
            return topology
        except Exception as e:
            print(f"Error reading CPU topology: {str(e)}")
            return {}
            
    def _read_sysfs(self, path: Path, default: str) -> str:
        """讀取 sysfs 文件內容"""
        try:
            return path.read_text().strip() if path.exists() else default
        except:
            return default

def get_cpu_freq() -> Dict[str, List[str]]:
    """獲取所有 CPU 核心的頻率信息"""
    freqs = {'current': [], 'min': [], 'max': []}
    try:
        cpu_path = Path('/sys/devices/system/cpu')
        for cpu_dir in sorted(cpu_path.glob('cpu[0-9]*')):
            freq_path = cpu_dir / 'cpufreq'
            if freq_path.exists():
                freqs['current'].append(
                    float(Path(freq_path / 'scaling_cur_freq').read_text()) / 1000
                )
                freqs['min'].append(
                    float(Path(freq_path / 'scaling_min_freq').read_text()) / 1000
                )
                freqs['max'].append(
                    float(Path(freq_path / 'scaling_max_freq').read_text()) / 1000
                )
        return freqs
    except Exception as e:
        print(f"Error reading CPU frequencies: {str(e)}")
        return freqs

def get_cpu_temp() -> List[Dict[str, str]]:
    """獲取 CPU 溫度信息"""
    temps = []
    try:
        result = subprocess.run(['sensors', '-j'], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for chip, sensors in data.items():
                if any('core' in key.lower() for key in sensors.keys()):
                    for sensor, values in sensors.items():
                        if 'core' in sensor.lower():
                            if isinstance(values, dict) and 'temp1_input' in values:
                                temps.append({
                                    'core': sensor,
                                    'temperature': f"{values['temp1_input']}°C"
                                })
    except FileNotFoundError:
        print("Warning: 'sensors' command not found. Install lm-sensors for temperature monitoring.")
    except Exception as e:
        print(f"Error getting CPU temperature: {str(e)}")
    return temps

def get_cpu_usage() -> Dict[str, float]:
    """獲取 CPU 使用率"""
    try:
        result = subprocess.run(['mpstat', '1', '1'], capture_output=True, text=True)
        usage = {}
        
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            for line in lines:
                if 'all' in line:
                    parts = line.split()
                    usage['user'] = float(parts[-7])
                    usage['system'] = float(parts[-6])
                    usage['idle'] = float(parts[-2])
                    usage['iowait'] = float(parts[-3])
                    break
        return usage
    except FileNotFoundError:
        print("Warning: 'mpstat' command not found. Install sysstat for detailed CPU usage.")
        return {}
    except Exception as e:
        print(f"Error getting CPU usage: {str(e)}")
        return {}

def get_cpu_governor() -> Dict[int, str]:
    """獲取 CPU 頻率調節器設置"""
    governors = {}
    try:
        cpu_path = Path('/sys/devices/system/cpu')
        for cpu_dir in sorted(cpu_path.glob('cpu[0-9]*')):
            cpu_num = int(cpu_dir.name[3:])
            governor_path = cpu_dir / 'cpufreq/scaling_governor'
            if governor_path.exists():
                governors[cpu_num] = governor_path.read_text().strip()
    except Exception as e:
        print(f"Error reading CPU governors: {str(e)}")
    return governors

def setup_parser():
    parser = argparse.ArgumentParser(description='CPU information and management tool')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show CPU information')
    info_parser.add_argument('-a', '--all', action='store_true',
                            help='Show all information including flags')
    
    # temp command
    subparsers.add_parser('temp', help='Show CPU temperature')
    
    # freq command
    subparsers.add_parser('freq', help='Show CPU frequency information')
    
    # usage command
    subparsers.add_parser('usage', help='Show CPU usage')
    
    # topology command
    subparsers.add_parser('topology', help='Show CPU topology')
    
    # governor command
    subparsers.add_parser('governor', help='Show CPU frequency governor settings')
    
    return parser

def show_usage():
    print("\nUsage:")
    print("  cpu info [-a]        - Show CPU information")
    print("  cpu temp             - Show CPU temperature")
    print("  cpu freq             - Show CPU frequency")
    print("  cpu usage            - Show CPU usage")
    print("  cpu topology         - Show CPU topology")
    print("  cpu governor         - Show CPU governor settings")
    print("\nExamples:")
    print("  cpu info")
    print("  cpu info -a")
    print("  cpu temp")
    print("  cpu freq")

def execute(args):
    if not args.command:
        show_usage()
        return 1
        
    try:
        if args.command == 'info':
            cpu = CPUInfo()
            print("\nCPU Information:")
            print(f"Model: {cpu.info.get('model', 'Unknown')}")
            print(f"Vendor: {cpu.info.get('vendor', 'Unknown')}")
            print(f"Current Frequency: {cpu.info.get('current_freq', 'Unknown')}")
            print(f"Maximum Frequency: {cpu.info.get('max_freq', 'Unknown')}")
            print(f"Cache Size: {cpu.info.get('cache', 'Unknown')}")
            
            if args.all and cpu.info.get('flags'):
                print("\nCPU Flags:")
                flags = sorted(cpu.info['flags'])
                for i in range(0, len(flags), 4):
                    print("  " + "  ".join(flags[i:i+4]))
                    
        elif args.command == 'temp':
            temps = get_cpu_temp()
            if temps:
                print("\nCPU Temperature:")
                print(f"{'Core':<10} {'Temperature'}")
                print("-" * 30)
                for temp in temps:
                    print(f"{temp['core']:<10} {temp['temperature']}")
            else:
                print("No temperature information available")
                
        elif args.command == 'freq':
            freqs = get_cpu_freq()
            if any(freqs.values()):
                print("\nCPU Frequencies:")
                print(f"{'CPU':<6} {'Current':<10} {'Min':<10} {'Max':<10}")
                print("-" * 40)
                for i in range(len(freqs['current'])):
                    print(f"CPU{i:<3} "
                          f"{freqs['current'][i]:>7.0f} MHz "
                          f"{freqs['min'][i]:>7.0f} MHz "
                          f"{freqs['max'][i]:>7.0f} MHz")
                          
        elif args.command == 'usage':
            usage = get_cpu_usage()
            if usage:
                print("\nCPU Usage:")
                print(f"User: {usage.get('user', 0):.1f}%")
                print(f"System: {usage.get('system', 0):.1f}%")
                print(f"I/O Wait: {usage.get('iowait', 0):.1f}%")
                print(f"Idle: {usage.get('idle', 0):.1f}%")
                
        elif args.command == 'topology':
            cpu = CPUInfo()
            if cpu.topology:
                print("\nCPU Topology:")
                print(f"{'CPU':<6} {'Core ID':<10} {'Package ID':<12} "
                      f"{'Thread Siblings':<16} {'Status'}")
                print("-" * 60)
                for cpu_num, info in sorted(cpu.topology.items()):
                    print(f"CPU{cpu_num:<3} "
                          f"{info['core_id']:<10} "
                          f"{info['physical_package_id']:<12} "
                          f"{info['thread_siblings']:<16} "
                          f"{'Online' if info['online'] else 'Offline'}")
                          
        elif args.command == 'governor':
            governors = get_cpu_governor()
            if governors:
                print("\nCPU Frequency Governors:")
                print(f"{'CPU':<6} {'Governor'}")
                print("-" * 25)
                for cpu_num, governor in sorted(governors.items()):
                    print(f"CPU{cpu_num:<3} {governor}")
                    
        return 0
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))
