# BIM Compliance Micro-Prototype

A web‑based tool for automated fire egress compliance checking of architectural models, built as a technical test for HKU AI+BIM team.

## Features

- **Two rules**:
  1. Minimum clear width of designated egress doors (default ≥850 mm)
  2. Maximum travel distance from any occupied space to the nearest exit (default ≤45 m)
- **Input formats**:
  - Simplified JSON (recommended, no external dependencies)
  - IFC (via `ifcopenshell`, requires sidecar adjacency file for travel distance)
- **Interactive web interface** built with Streamlit
- **Visual egress diagram** highlighting violations

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   
## Run:
  streamlit run app.py

## Usage:

Upload a JSON or IFC file.

Adjust thresholds in the sidebar.

View violations and the connectivity diagram.

Download a JSON report.

## Sample data:

data/sample_building_pass.json – all rules pass.

data/sample_building_fail.json – contains violations.

## Design choices:

Adapter pattern – decouples JSON/IFC input from rule logic.

Graph‑based travel distance – more realistic than Euclidean, catches unreachable spaces.

All thresholds are configurable in data/config.yaml and the UI
