import argparse
from datetime import datetime

def setup_parser():
    parser = argparse.ArgumentParser(description='Show current time')
    parser.add_argument('--format', type=str, default='%Y-%m-%d %H:%M:%S',
                      help='DateTime format string')
    parser.add_argument('--utc', action='store_true',
                      help='Show UTC time instead of local time')
    return parser

def execute(args):
    current_time = datetime.utcnow() if args.utc else datetime.now()
    print(current_time.strftime(args.format))

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)