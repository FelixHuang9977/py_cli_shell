import argparse
import subprocess

def run_usb_all():
    command = [ '.venv/bin/python','diag_cli.py','run','usb']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {str(e)}")

def run_cpu_all():
    command = [ '.venv/bin/python','diag_cli.py','run','cpu']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {str(e)}")
        
def setup_parser():
    parser = argparse.ArgumentParser(description='run usb test cases')
    parser.add_argument('testcase', type=str, help='all or specific testcases')
    return parser

def execute(args):
    testcase = args.category or "all"
    if testcase == 'all':
        run_usb_all()
    else:
        print(f"Unknown command: {testcase}, or TODO!!!")


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)