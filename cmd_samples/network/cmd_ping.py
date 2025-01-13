import argparse
import platform
import subprocess

def setup_parser():
    parser = argparse.ArgumentParser(description='Ping a host')
    parser.add_argument('host', help='Host to ping')
    parser.add_argument('--count', '-c', type=int, default=4,
                      help='Number of packets to send')
    return parser

def execute(args):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(args.count), args.host]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)