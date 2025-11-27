from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hello World Test</title>
    </head>
    <body>
        <h1>FastAPI Test Page</h1>
        <button onclick="document.getElementById('output').innerText='Hello World!'">
            Click Me
        </button>
        <p id="output"></p>
    </body>
    </html>
    """
