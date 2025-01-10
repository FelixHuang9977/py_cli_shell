import argparse

def setup_parser():
    parser = argparse.ArgumentParser(description='Simple calculator')
    parser.add_argument('expression', type=str, help='Math expression to evaluate')
    return parser

def execute(args):
    try:
        # 使用 eval 要注意安全性，這裡只是示範
        result = eval(args.expression)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)