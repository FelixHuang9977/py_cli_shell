import argparse
import psutil

def setup_parser():
    parser = argparse.ArgumentParser(description='Show disk usage')
    parser.add_argument('--path', default='/',
                      help='Path to check disk usage')
    parser.add_argument('--human-readable', '-h', action='store_true',
                      help='Show sizes in human readable format')
    return parser

def human_size(bytes_):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_ < 1024:
            return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}PB"

def execute(args):
    try:
        usage = psutil.disk_usage(args.path)
        if args.human_readable:
            total = human_size(usage.total)
            used = human_size(usage.used)
            free = human_size(usage.free)
        else:
            total = f"{usage.total} bytes"
            used = f"{usage.used} bytes"
            free = f"{usage.free} bytes"

        print(f"Disk usage for {args.path}:")
        print(f"Total: {total}")
        print(f"Used:  {used}")
        print(f"Free:  {free}")
        print(f"Usage: {usage.percent}%")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)