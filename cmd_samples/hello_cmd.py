#hello_cmd.py
import argparse

def get_main_parser():
    parser = argparse.ArgumentParser(prog="hello")
    parser.add_argument(
        "who", help="good question", nargs="?", default="world")
    parser.add_argument(
        "--what", help="a better question", default="hello",
        choices=["hello", "goodbye"])
    return parser

if __name__ == "__main__":
    parser = get_main_parser()
    args = parser.parse_args()
    print("{}, {}!".format(args.what, args.who))