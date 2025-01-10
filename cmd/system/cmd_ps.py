import argparse
import psutil

def setup_parser():
    parser = argparse.ArgumentParser(description='List processes')
    parser.add_argument('--sort', choices=['cpu', 'memory', 'pid', 'name'],
                      default='cpu', help='Sort criteria')
    parser.add_argument('--top', type=int, default=10,
                      help='Show only top N processes')
    return parser

def execute(args):
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    processes.sort(key=lambda x: x.get(
        {'cpu': 'cpu_percent',
         'memory': 'memory_percent',
         'pid': 'pid',
         'name': 'name'}[args.sort]
    ) or 0, reverse=True)

    print(f"{'PID':>7} {'CPU%':>7} {'MEM%':>7} {'NAME':<20}")
    print("-" * 45)
    
    for proc in processes[:args.top]:
        print(f"{proc['pid']:>7} {proc.get('cpu_percent', 0):>7.1f} "
              f"{proc.get('memory_percent', 0):>7.1f} {proc['name']:<20}")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)