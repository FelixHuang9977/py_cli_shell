import argparse
import subprocess

def run_usb_all():
    """執行所有 USB 測試案例"""
    command = ['.venv/bin/python', 'diag_test.py', 'run', 'usb']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error running USB tests: {str(e)}")

def run_cpu_all():
    """執行所有 CPU 測試案例"""
    command = ['.venv/bin/python', 'diag_test.py', 'run', 'cpu']
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error running CPU tests: {str(e)}")
        
def show_usage():
    """顯示使用說明"""
    print("\nUsage:")
    print("  run <category>")
    print("\nAvailable categories:")
    print("  usb    - Run USB test cases")
    print("  cpu    - Run CPU test cases")
    print("  all    - Run all test cases")
    print("\nExamples:")
    print("  run usb")
    print("  run cpu")
    print("  run all")

def setup_parser():
    parser = argparse.ArgumentParser(description='Run diagnostic test cases')
    parser.add_argument('category', 
                       nargs='?',  # 使參數可選
                       choices=['usb', 'cpu', 'all'],
                       help='Test category: usb, cpu, or all')
    return parser

def execute(args):
    # 如果沒有提供參數，顯示使用說明並返回
    if not args.category:
        show_usage()
        return 1
    
    category = args.category.lower()
    
    if category == 'all':
        print("Running all test cases...")
        run_usb_all()
        run_cpu_all()
    elif category == 'usb':
        print("Running USB test cases...")
        run_usb_all()
    elif category == 'cpu':
        print("Running CPU test cases...")
        run_cpu_all()
    else:
        print(f"Unknown test category: {category}")
        show_usage()
        return 1

    return 0

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    exit(execute(args))