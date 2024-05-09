import argparse
import json
parser = argparse.ArgumentParser()
parser.add_argument('--type', type=str, choices=['asset', 'asset_type'], required=True)