from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import tempfile, os, csv, yaml, base64, zlib
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
from diagram_utils import generate_diagram

app = FastAPI()

@app.post("/upload-csv/")
async def upload_csv(file: UploadFile = File(...)):
    # Save uploaded CSV to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        tmp_csv.write(await file.read())
        tmp_csv_path = tmp_csv.name

    # Load config.yaml (kept in project root)
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    # Parse CSV
    with open(tmp_csv_path) as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Group data by Header → Sub-Header
    grouped = {}
    for row in data:
        h = row["Header"]
        s = row["Sub-Header"]
        grouped.setdefault(h, {}).setdefault(s, []).append(row)

    # Build drawio XML
    drawio_root = Element("mxfile", {
        "host": "app.diagrams.net",
        "modified": "2025-11-27T22:00:00Z",
        "agent": "fastapi",
        "version": "20.6.3",
        "type": "device"
    })

    for header, sub_map in grouped.items():
        diagram_bytes = generate_diagram(config, header, sub_map)
        compressed = zlib.compress(diagram_bytes)[2:-4]
        encoded = base64.b64encode(compressed).decode("utf-8")
        diagram_element = Element("diagram", {"name": header})
        diagram_element.text = encoded
        drawio_root.append(diagram_element)

    final_xml = tostring(drawio_root, encoding="unicode")
    pretty_xml = minidom.parseString(final_xml).toprettyxml(indent="  ")

    # Save to temp .drawio file
    tmp_drawio = tempfile.NamedTemporaryFile(delete=False, suffix=".drawio")
    with open(tmp_drawio.name, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    # Clean up CSV temp file
    os.remove(tmp_csv_path)

    # Return file for download
    return FileResponse(tmp_drawio.name, filename="output.drawio")
    
