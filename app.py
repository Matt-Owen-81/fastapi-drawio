from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
import tempfile, os, csv, yaml, base64, zlib
from xml.etree.ElementTree import Element, tostring
from xml.dom import minidom
from diagram_utils import generate_diagram

app = FastAPI()

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
        <form action="/generate-download/" enctype="multipart/form-data" method="post">
            <input name="file" type="file" accept=".csv">
            <input type="submit" value="Generate & Download">
        </form>
        <br>
        <form action="/generate-open/" enctype="multipart/form-data" method="post">
            <input name="file" type="file" accept=".csv">
            <input type="submit" value="Generate & Open in diagrams.net">
        </form>
    </body>
    </html>
    """

def build_drawio(file_bytes: bytes, config_path="config.yaml"):
    # Save uploaded CSV to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
        tmp_csv.write(file_bytes)
        tmp_csv_path = tmp_csv.name

    # Load config.yaml
    with open(config_path) as f:
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

    os.remove(tmp_csv_path)
    return tmp_drawio.name

@app.post("/generate-download/")
async def generate_download(file: UploadFile = File(...)):
    path = build_drawio(await file.read())
    return FileResponse(path, filename="output.drawio")

@app.post("/generate-open/")
async def generate_open(file: UploadFile = File(...)):
    path = build_drawio(await file.read())
    # Serve the file at /files/<filename>
    filename = os.path.basename(path)
    return RedirectResponse(
        url=f"https://app.diagrams.net/?url=http://127.0.0.1:8000/files/{filename}"
    )

@app.get("/files/{filename}")
async def serve_file(filename: str):
    filepath = os.path.join(tempfile.gettempdir(), filename)
    return FileResponse(filepath, filename=filename)
