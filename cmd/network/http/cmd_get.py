import argparse
import requests

def setup_parser():
    parser = argparse.ArgumentParser(description='Make HTTP GET request')
    parser.add_argument('url', help='URL to request')
    parser.add_argument('--headers', '-H', action='append',
                      help='Headers in format "key:value"')
    return parser

def execute(args):
    headers = {}
    if args.headers:
        for header in args.headers:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    
    try:
        response = requests.get(args.url, headers=headers)
        print(f"Status: {response.status_code}")
        print("Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print("\nContent:")
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()
    execute(args)