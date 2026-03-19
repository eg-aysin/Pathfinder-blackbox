# EnerKey – Mass Import Tool

A demo system of 4 microservices that pull data from two sources, merge it, and return a combined Excel file.

## Architecture

```
EnerKey (8000)  →  Pathfinder (8001)  →  Salesforce Mock (8003)
                                       →  Record Box (8002)
                        ↓
                   Merged output.xlsx
```

| Service | Port | Role |
|---|---|---|
| EnerKey | 8000 | User-facing Bootstrap UI. |
| Pathfinder | 8001 | Orchestrator – fans out, merges, returns xlsx |
| Record Box | 8002 | Returns NetSuite mapping data (file2) |
| Salesforce Mock | 8003 | Returns sales line item data (file1) |

## Setup

```bash
pip install -r enerkey/requirements.txt
pip install -r pathfinder/requirements.txt
pip install -r recordbox/requirements.txt
pip install -r salesforce_mock/requirements.txt
```

Or use `install.bat` on Windows.

## Run

```bash
python start.py
```

Opens all 4 services and launches the browser at `http://localhost:8000`.

## How it works

1. Enter a facility name in EnerKey and click **Mass Import**
2. EnerKey calls Pathfinder with the facility name
3. Pathfinder queries Salesforce and Record Box **in parallel**
4. Results are merged on `Facility name / Account name` + `Sales Items ID`
5. A 10-column `output.xlsx` is returned for download
