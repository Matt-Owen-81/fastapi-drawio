import csv
import yaml
import uuid
import base64
import zlib
import subprocess
import argparse
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# --- your existing helper functions (create_cell, create_edge, generate_diagram) go here ---

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
        'host': 'app.diagrams.net',
        'modified': '2025-11-27T22:00:00Z',
        'agent': 'python',
        'version': '20.6.3',
        'type': 'device'
    })

    for header, sub_map in grouped.items():
        diagram_bytes = generate_diagram(config, header, sub_map)
        compressed = zlib.compress(diagram_bytes)[2:-4]
        encoded = base64.b64encode(compressed).decode('utf-8')
        diagram_element = Element('diagram', {'name': header})
        diagram_element.text = encoded
        drawio_root.append(diagram_element)

    # Save to file
    final_xml = tostring(drawio_root, encoding='unicode')
    pretty_xml = minidom.parseString(final_xml).toprettyxml(indent="  ")
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

    print(f"✅ Diagram saved to {args.output}")

    # Try to open automatically (Ubuntu: xdg-open)
    try:
        subprocess.run(["xdg-open", args.output], check=False)
    except Exception as e:
        print(f"Could not auto-open file: {e}")

if __name__ == "__main__":
    main()
