from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="Salesforce Mock")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent.parent / "file1.xlsx"


def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name="File1")
    return df


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Salesforce – Blackbox</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
        body { background: #0d1117; color: #c9d1d9; font-family: monospace; }
        .box { border: 1px solid #30363d; border-radius: 8px; padding: 2rem; max-width: 600px; margin: 4rem auto; }
        h1 { color: #58a6ff; }
        .badge-sf { background: #00a1e0; }
        code { color: #7ee787; }
      </style>
    </head>
    <body>
      <div class="box">
        <h1>&#9749; Salesforce</h1>
        <span class="badge badge-sf text-white px-3 py-1 rounded mb-3 d-inline-block" style="background:#00a1e0">BLACKBOX</span>
        <p class="mt-3 text-secondary">This service simulates the Salesforce data source. It exposes sales line item records (pricing, quantities, dates) filtered by facility name.</p>
        <hr style="border-color:#30363d">
        <p><strong>Endpoint:</strong><br><code>GET /api/data?facility_name=&lt;name&gt;</code></p>
        <p><strong>Returns:</strong> Sales items — ID, display name, start date, currency, quantity, rate.</p>
        <a href="/docs" class="btn btn-sm btn-outline-info mt-2">API Docs</a>
      </div>
    </body>
    </html>
    """


@app.get("/api/data")
def get_data(facility_name: str = ""):
    df = load_data()
    if facility_name:
        mask = df["Facility name / Account name"].str.contains(
            facility_name, case=False, na=False
        )
        filtered = df[mask]
        if not filtered.empty:
            df = filtered
    return df.to_dict(orient="records")


@app.get("/health")
def health():
    return {"status": "ok", "service": "salesforce-mock"}
