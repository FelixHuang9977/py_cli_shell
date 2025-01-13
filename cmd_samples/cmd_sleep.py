import argparse
import time
import sys
def setup_parser():
    parser = argparse.ArgumentParser(description='Sleep for specified seconds, simon')
    parser.add_argument('delay', type=int, help='<int>, delay in seconds, simon')
    return parser

def execute(args):
    total_seconds = args.delay
    try:
        for remaining in range(total_seconds, 0, -1):
            sys.stdout.write(f'\rSleeping for {remaining} seconds... ')
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\rDone sleeping.              \n')  # 清除行
    except KeyboardInterrupt:
        sys.stdout.write('\rSleep interrupted.          \n')  # 清除行
        return
    
if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)