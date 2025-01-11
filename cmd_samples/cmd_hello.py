import argparse

def setup_parser():
    parser = argparse.ArgumentParser(description='A simple hello command')
    parser.add_argument('--name', type=str, help='Name to greet')
    parser.add_argument('--count', type=int, default=1, help='Number of times to greet')
    return parser

def execute(args):
    name = args.name or "World"
    for _ in range(args.count):
        print(f"Hello, {name}!")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)