import io
import json
import sys
from pathlib import Path

import streamlit as st
import yaml
import matplotlib.pyplot as plt

from core.schema import Building
from core.adapters.json_adapter import load_json_building, building_from_dict
from core.adapters.ifc_adapter import load_ifc_building
from core.engine import run_checks
from core.visualize import render_floor_diagram

st.set_page_config(page_title="BIM Compliance Checker", layout="wide")
st.title("🏗️ BIM Compliance Micro-Prototype")
st.markdown("Check fire egress rules: **door width** and **travel distance**.")

# Load default config
CONFIG_PATH = Path("data/config.yaml")
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        default_config = yaml.safe_load(f)
else:
    default_config = {"min_clear_width_mm": 850, "max_travel_distance_m": 45}

# Sidebar for configuration
st.sidebar.header("Rule Thresholds")
config = {
    "min_clear_width_mm": st.sidebar.number_input(
        "Minimum clear door width (mm)", value=default_config.get("min_clear_width_mm", 850), step=10
    ),
    "max_travel_distance_m": st.sidebar.number_input(
        "Maximum travel distance to exit (m)", value=default_config.get("max_travel_distance_m", 45), step=1
    ),
}

# File upload
uploaded_file = st.file_uploader("Upload a building model (JSON or IFC)", type=["json", "ifc"])

if uploaded_file is not None:
    file_ext = Path(uploaded_file.name).suffix.lower()
    try:
        if file_ext == ".json":
            # Read JSON from uploaded file
            data = json.load(uploaded_file)
            building = building_from_dict(data, source_file=uploaded_file.name)
        elif file_ext == ".ifc":
            # Save uploaded IFC to a temporary file
            temp_ifc = Path(f"/tmp/{uploaded_file.name}")
            temp_ifc.write_bytes(uploaded_file.getvalue())
            # Try to load with ifcopenshell; if fails, show error and suggest JSON
            try:
                building = load_ifc_building(temp_ifc)
            except ImportError:
                st.error("IFC support requires `ifcopenshell`. Please install it or use a JSON file.")
                st.stop()
            except Exception as e:
                st.error(f"Failed to parse IFC: {e}")
                st.stop()
        else:
            st.error("Unsupported file type. Please upload .json or .ifc.")
            st.stop()

        st.success(f"Loaded building: **{building.name}** ({len(building.spaces)} spaces, {len(building.doors)} doors)")

        # Run checks
        report = run_checks(building, config)

        # Display summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Violations", report.total_violations)
        col2.metric("Passed", "✅" if report.passed else "❌")
        col3.metric("Rules Checked", len(report.rule_results))

        # Show violation details
        if report.total_violations > 0:
            st.subheader("Violations")
            for result in report.rule_results:
                if result.violations:
                    st.write(f"**{result.rule_name}**")
                    for v in result.violations:
                        severity_emoji = "🔴" if v.severity == "critical" else "🟠"
                        st.write(f"{severity_emoji} {v.message}")
        else:
            st.success("All checks passed!")

        # Visualize
        st.subheader("Egress Connectivity Diagram")
        fig = render_floor_diagram(building, report)
        st.pyplot(fig)

        # Download report
        report_json = json.dumps(report.to_dict(), indent=2)
        st.download_button(
            label="Download Report (JSON)",
            data=report_json,
            file_name="compliance_report.json",
            mime="application/json",
        )

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.stop()
else:
    st.info("👈 Upload a JSON or IFC file to start checking.")
    # Show sample data info
    st.markdown("### Sample JSON format")
    st.code("""{
  "name": "Sample Office",
  "spaces": [
    {"id": "S1", "name": "Office 101", "centroid": {"x": 0, "y": 0}, "area_m2": 20, "is_exit": false},
    {"id": "S2", "name": "Corridor", "centroid": {"x": 5, "y": 0}, "area_m2": 15, "is_exit": false},
    {"id": "S3", "name": "Stair A", "centroid": {"x": 10, "y": 0}, "area_m2": 10, "is_exit": true}
  ],
  "doors": [
    {"id": "D1", "name": "Door 1", "width_mm": 900, "connects": ["S1", "S2"], "is_designated_exit": false},
    {"id": "D2", "name": "Exit Door", "width_mm": 800, "connects": ["S2", "S3"], "is_designated_exit": true}
  ]
}""")