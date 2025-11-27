from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import os, csv, yaml, base64, zlib
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
from diagram_utils import generate_diagram

app = FastAPI()

LATEST_FILE = "latest.drawio"  # stable filename served at /latest.drawio

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSV → Draw.io Generator</title>
    </head>
    <body>
        <h1>Upload CSV to Generate Draw.io</h1>
        <form enctype="multipart/form-data" method="post">
            <input name="file" type="file" accept=".csv">
            <br><br>
            <button formaction="/generate-download/" type="submit">Generate & Download</button>
            <button formaction="/generate-open/" type="submit">Generate & Open in diagrams.net</button>
        </form>
    </body>
    </html>
    """

def build_drawio(file_bytes: bytes, config_path="config.yaml", output_path=LATEST_FILE):
    # Save uploaded CSV temporarily
    tmp_csv = "tmp.csv"
    with open(tmp_csv, "wb") as f:
        f.write(file_bytes)

    # Load config.yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Parse CSV
    with open(tmp_csv) as f:
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

    # Save to stable file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    os.remove(tmp_csv)
    return output_path

@app.post("/generate-download/")
async def generate_download(file: UploadFile = File(...)):
    path = build_drawio(await file.read())
    return FileResponse(path, filename="output.drawio")

@app.post("/generate-open/")
async def generate_open(file: UploadFile = File(...)):
    path = build_drawio(await file.read())
    # Redirect to diagrams.net with public URL to /latest.drawio
    # Replace 192.168.1.10 with your server’s IP or hostname
    server_url = "http://192.168.1.10:8000/latest.drawio"
    return RedirectResponse(url=f"https://app.diagrams.net/?url={server_url}")

@app.get("/latest.drawio")
async def serve_latest():
    return FileResponse(LATEST_FILE, filename="output.drawio")
