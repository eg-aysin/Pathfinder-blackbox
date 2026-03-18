import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
import httpx
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="EnerKey")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PATHFINDER_URL = os.getenv("PATHFINDER_URL", "http://localhost:8001")
HTML_FILE = Path(__file__).parent / "templates" / "index.html"


class ImportRequest(BaseModel):
    facility_name: str


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_FILE.read_text(encoding="utf-8"))


@app.post("/api/import")
async def mass_import(data: ImportRequest):
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{PATHFINDER_URL}/api/import",
            json={"facility_name": data.facility_name},
        )
    if response.status_code != 200:
        return JSONResponse(
            status_code=502,
            content={"error": f"Pathfinder returned {response.status_code}: {response.text}"},
        )

    safe_name = data.facility_name.replace(" ", "_").replace("/", "-")
    return StreamingResponse(
        iter([response.content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="output_{safe_name}.xlsx"'
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "enerkey"}
