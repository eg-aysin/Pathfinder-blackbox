from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(title="Record Box")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent.parent / "file2.xlsx"


def load_data() -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name="File2")
    return df


@app.get("/", response_class=HTMLResponse)
def index():
    df = load_data()
    facilities = sorted(df["Facility name / Account name"].dropna().unique().tolist())
    rows_html = "".join(
        f"<tr>"
        f"<td>{r['Facility name / Account name']}</td>"
        f"<td><code>{r['Sales Items ID']}</code></td>"
        f"<td><code>{r['NetSuite account ID']}</code></td>"
        f"<td><code>{r['NetSuite subscription ID']}</code></td>"
        f"<td><code>{r['NetSuite subscription item ID']}</code></td>"
        f"</tr>"
        for _, r in df.iterrows()
    )
    fac_badges = "".join(
        f'<span class="badge bg-secondary me-1 mb-1">{f}</span>' for f in facilities
    )
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Record Box</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
        body {{ background: #1a1a2e; color: #eaeaea; }}
        .navbar {{ background: #16213e !important; }}
        .card {{ background: #16213e; border: 1px solid #0f3460; }}
        h1, h5 {{ color: #e94560; }}
        table {{ font-size: 0.82rem; }}
        thead {{ background: #0f3460; color: #eaeaea; }}
        code {{ color: #f0a500; }}
      </style>
    </head>
    <body>
      <nav class="navbar navbar-dark px-4 py-3">
        <span class="navbar-brand fw-bold fs-4">&#128230; Record Box</span>
        <span class="badge bg-warning text-dark">INTERNAL SERVICE – PORT 8002</span>
      </nav>
      <div class="container mt-4">
        <div class="row g-4">
          <div class="col-md-4">
            <div class="card p-4 h-100">
              <h5>About</h5>
              <p class="text-secondary small">Record Box stores NetSuite mapping data — it links Facility + Sales Item IDs to their corresponding NetSuite account, subscription, and subscription item IDs.</p>
              <hr style="border-color:#0f3460">
              <h5>Facilities ({len(facilities)})</h5>
              <div>{fac_badges}</div>
              <hr style="border-color:#0f3460">
              <p class="mb-1"><strong>Endpoint</strong></p>
              <code class="small">GET /api/records?facility_name=&lt;name&gt;</code>
              <a href="/docs" class="btn btn-sm btn-outline-warning mt-3">API Docs</a>
            </div>
          </div>
          <div class="col-md-8">
            <div class="card p-4">
              <h5>All Records ({len(df)} rows)</h5>
              <div class="table-responsive mt-2">
                <table class="table table-dark table-sm table-hover">
                  <thead>
                    <tr>
                      <th>Facility</th>
                      <th>Sales Item ID</th>
                      <th>NS Account</th>
                      <th>NS Subscription</th>
                      <th>NS Sub Item</th>
                    </tr>
                  </thead>
                  <tbody>{rows_html}</tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """


@app.get("/api/records")
def get_records(facility_name: str = ""):
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
    return {"status": "ok", "service": "record-box"}
