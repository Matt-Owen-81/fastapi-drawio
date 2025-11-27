import csv
import yaml
import base64
import zlib
import subprocess
import argparse
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
from diagram_utils import generate_diagram

def main():
    parser = argparse.ArgumentParser(description="Generate Draw.io diagram from CSV + YAML config")
    parser.add_argument("csv_file", help="Path to CSV file")
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to YAML config file")
    parser.add_argument("-o", "--output", default="diagram.drawio", help="Output .drawio file")
    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Load CSV
    with open(args.csv_file) as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Group data by Header → Subheader
    grouped = {}
    for row in data:
        h = row['Header']
        s = row['Sub-Header']
        grouped.setdefault(h, {}).setdefault(s, []).append(row)

    # Create multi-page drawio file
    drawio_root = Element('mxfile', {
        'host': 'app.di
