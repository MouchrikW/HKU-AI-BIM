
# AI Prompts Used

This project was built with AI assistance (Claude) as part of the HKU AI+BIM technical test. The following prompts guided the development:

1. **Architecture** – “Design a Python/Streamlit tool with adapter pattern, canonical schema, and rule engine for BIM compliance (door width and travel distance).”

2. **Schema & Adapters** – “Create `Building` schema with `Space`, `Door`, `Point2D`. Implement JSON and IFC adapters (using `ifcopenshell`). For IFC, read adjacency from a sidecar file.”

3. **Rules** – “Implement two rules: (a) exit door width check against configurable minimum; (b) graph‑based shortest path travel distance to nearest exit (flag unreachable spaces as `critical`).”

4. **Visualisation** – “Render a schematic floor plan with rooms as rectangles, doors as lines, colour‑coded by violation status (Matplotlib).”

5. **Web UI** – “Build a Streamlit app with file upload, adjustable thresholds, violation list, diagram, and JSON export.”

6. **Testing** – “Create sample JSON files (pass/fail) and unit tests.”

7. **Documentation** – “Write README with setup/run instructions and a `prompts.md` file.”

All code was generated and iteratively refined through these prompts, with manual adjustments for consistency and quality.
