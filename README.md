# BIM Egress Compliance Checker

A micro‑prototype for the HKU AI+BIM technical test. Checks two fire‑egress rules:

1. **Egress door width** – flags exit doors narrower than a configurable minimum (default 850 mm).
2. **Travel distance to nearest exit** – graph‑based shortest path over actual door connectivity (default max 45 m). Unreachable spaces are flagged as `critical`.

## Installation

git clone https://github.com/MouchrikW/HKU-AI-BIM.git
cd HKU-AI-BIM
python -m venv venv
# Windows: venv\Scripts\activate  |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

Run:

streamlit run app.py
