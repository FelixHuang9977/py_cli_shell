import argparse
from datetime import datetime

def setup_parser():
    parser = argparse.ArgumentParser(description='Show current time')
    parser.add_argument('--format', type=str, default='%Y-%m-%d %H:%M:%S',
                      help='DateTime format string')
    return parser

def execute(args):
    print(datetime.now().strftime(args.format))

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)