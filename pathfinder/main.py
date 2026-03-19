import asyncio
import io
import os
from pathlib import Path

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Pathfinder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SALESFORCE_URL = os.getenv("SALESFORCE_URL", "http://localhost:8003")
RECORDBOX_URL = os.getenv("RECORDBOX_URL", "http://localhost:8002")


class ImportRequest(BaseModel):
    facility_name: str


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Pathfinder</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
        body { background: #0f1923; color: #cdd6f4; }
        .navbar { background: #1e2d3d !important; }
        .card { background: #1e2d3d; border: 1px solid #2a4a6b; }
        h1, h5 { color: #89b4fa; }
        .arrow { color: #89b4fa; font-size: 1.5rem; }
        .node { background: #2a4a6b; border-radius: 8px; padding: 0.6rem 1.2rem; display: inline-block; font-weight: 600; }
        code { color: #a6e3a1; }
        .badge-pf { background: #89b4fa; }
      </style>
    </head>
    <body>
      <nav class="navbar navbar-dark px-4 py-3">
        <span class="navbar-brand fw-bold fs-4">&#9889; Pathfinder</span>
        <span class="badge text-dark badge-pf">ORCHESTRATOR – PORT 8001</span>
      </nav>
      <div class="container mt-5">
        <div class="row justify-content-center">
          <div class="col-md-8">
            <div class="card p-4 mb-4">
              <h5>What Pathfinder does</h5>
              <p class="text-secondary small">Pathfinder is the central orchestrator. It receives a facility name from EnerKey, fans out parallel requests to Salesforce and Record Box, then merges the two datasets on <code>Facility name / Account name</code> + <code>Sales Items ID</code> and streams back the merged <code>output.xlsx</code>.</p>
            </div>
            <div class="card p-4 mb-4">
              <h5>Data Flow</h5>
              <div class="d-flex align-items-center flex-wrap gap-2 mt-3">
                <span class="node" style="background:#1a3a2a;color:#a6e3a1">EnerKey</span>
                <span class="arrow">&#8594;</span>
                <span class="node" style="background:#2a4a6b;color:#89b4fa">Pathfinder</span>
                <span class="arrow">&#8594;</span>
                <div class="d-flex flex-column gap-1">
                  <span class="node" style="background:#00a1e0;color:#fff">Salesforce</span>
                  <span class="node" style="background:#3d2b1a;color:#f0a500">Record Box</span>
                </div>
                <span class="arrow">&#8594;</span>
                <span class="node" style="background:#1a3a2a;color:#a6e3a1">Merge &#8594; output.xlsx</span>
              </div>
            </div>
            <div class="card p-4">
              <h5>Endpoint</h5>
              <code>POST /api/import</code>
              <p class="text-secondary small mt-2">Body: <code>{"facility_name": "..."}</code><br>
              Returns: <code>output.xlsx</code> — merged data with all 10 columns.</p>
              <a href="/docs" class="btn btn-sm btn-outline-info mt-2">API Docs</a>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """


@app.post("/api/import")
async def mass_import(data: ImportRequest):
    async with httpx.AsyncClient(timeout=60.0) as client:
        sf_task = client.get(
            f"{SALESFORCE_URL}/api/data",
            params={"facility_name": data.facility_name},
        )
        rb_task = client.get(
            f"{RECORDBOX_URL}/api/records",
            params={"facility_name": data.facility_name},
        )
        sf_resp, rb_resp = await asyncio.gather(sf_task, rb_task)

    if sf_resp.status_code != 200:
        raise HTTPException(502, f"Salesforce error: {sf_resp.text}")
    if rb_resp.status_code != 200:
        raise HTTPException(502, f"Record Box error: {rb_resp.text}")

    df1 = pd.DataFrame(sf_resp.json())
    df2 = pd.DataFrame(rb_resp.json())

    merge_keys = ["Facility name / Account name", "Sales Items ID"]
    merged = pd.merge(df1, df2, on=merge_keys, how="outer")

    # Add 'Cost' column as Quantity * Rate (Unit price)
    quantity_col = next((col for col in merged.columns if col.lower() == "quantity"), None)
    rate_col = next((col for col in merged.columns if "rate" in col.lower()), None)
    if quantity_col and rate_col:
      merged["Cost"] = merged[quantity_col].astype(float) * merged[rate_col].astype(float)
    else:
      merged["Cost"] = None  # or raise an error if preferred

    # Reorder columns to match file3 format and include 'Cost'
    desired_order = [
      "Facility name / Account name",
      "Sales Items ID",
      "Sales item display name",
      "NetSuite account ID",
      "NetSuite subscription ID",
      "NetSuite subscription item ID",
      "Start date",
      "Currency",
      "Quantity",
      "Rate (Unit price)",
      "Cost",
    ]
    final_cols = [c for c in desired_order if c in merged.columns] + [
      c for c in merged.columns if c not in desired_order
    ]
    merged = merged[final_cols]

    # Null value validation
    if merged.isnull().values.any():
      null_cols = merged.columns[merged.isnull().any()].tolist()
      raise HTTPException(400, f"Null values detected in columns: {', '.join(null_cols)}. Please check your data.")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      merged.to_excel(writer, index=False, sheet_name="Data")
    output.seek(0)

    safe_name = data.facility_name.replace(" ", "_").replace("/", "-")
    return StreamingResponse(
      output,
      media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      headers={
        "Content-Disposition": f'attachment; filename="output_{safe_name}.xlsx"'
      },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "pathfinder"}
