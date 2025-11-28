from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
import os, csv, yaml, base64, zlib
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
from diagram_utils import generate_diagram

app = FastAPI()

LATEST_FILE = "latest.drawio"

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
            <button formaction="/generate/" type="submit">Generate Diagram</button>
        </form>
    </body>
    </html>
    """

def build_drawio(file_bytes: bytes, config_path="config.yaml", output_path=LATEST_FILE):
    tmp_csv = "tmp.csv"
    with open(tmp_csv, "wb") as f:
        f.write(file_bytes)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    with open(tmp_csv) as f:
        reader = csv.DictReader(f)
        data = list(reader)

    grouped = {}
    for row in data:
        h = row["Header"]
        s = row["Sub-Header"]
        grouped.setdefault(h, {}).setdefault(s, []).append(row)

    drawio_root = Element("mxfile", {
        "host": "app.diagrams.net",
        "modified": "2025-11-28T09:00:00Z",
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    os.remove(tmp_csv)
    return output_path

@app.post("/generate/")
async def generate(file: UploadFile = File(...)):
    path = build_drawio(await file.read())
    # Return the file directly — browser downloads, desktop app opens if associated
    return FileResponse(path, filename="output.drawio", media_type="application/xml")
