# Helium Companion — V3 physics and design exploration

**15 October 2026 | Research revision, not a flight-qualified design**

Start with `DESIGN_REVIEW.md`, then `hardware/EXPERIMENT_PLAN.md`.

This revision explores factory-integrated sealing films, seam-only bonding, larger geared propellers, measured docking trim, four independently commanded motion axes, equal-volume prolate geometry, and closed-gas thermal constraints. It does not replace the v1 media firmware with tested flight software. No physical assembly, new physical measurement, email, purchase, CFD validation, or autonomous flight test was performed.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m engineering.model
python -m pytest -q
```

Run from this directory. Numerical outputs are regenerated in `reports/`. The v2 equations and historic motor data are frozen in `reference/v2_model.py` for traceability.

## Evidence hierarchy

`SUPPLIER_DATA`: a manufacturer's or seller's reported measurement/specification, not our assembly.
`CALCULATED`: geometry, conserved quantities, and numerical integration.
`ASSUMPTION`: an explicitly selected operating, material, or efficiency parameter.
`PHYSICALLY_VERIFIED`: none in this package.

The empty `reports/physical_measurements.csv` is intentional. The test suite uses synthetic data only to verify interpolation software; synthetic records are labeled and never counted as hardware measurements. Measurement ingestion rejects empty datasets, mismatched direction/guard conditions, and extrapolation beyond the measured voltage/thrust region.

## Files

- `engineering/model.py`: reduced-order physics and design sweeps.
- `engineering/measurements.py`: real-data validation and bounded interpolation.
- `tests/test_models.py`: analytic invariants, numerical checks, data-map boundary tests.
- `procurement/components_v3.csv`: component decisions, mass allocations, sourcing status.
- `procurement/MATERIAL_RFQ_V3.md`: unsent material/converter inquiry.
- `procurement/PROPULSION_RFQ.md`: unsent request for fitted gearbox/prop assemblies.
- `hardware/EXPERIMENT_PLAN.md`: discriminating tests and acceptance criteria.
- `hardware/PIN_AND_POWER_CONTRACT.md`: preliminary pin allocation and power constraints.
- `sources.md`: primary source links and limitations.

The spreadsheet uses formula-driven geometry/power calculations and separately labels imported simulation outputs. It is not firmware, a safety certification, or a measured endurance report.


`DESIGN_REVIEW.html` is a self-contained reading copy including the experiment protocol and plots. `helium_companion_v3.xlsx` contains nine formula-driven and evidence-tracking sheets. The Python model owns the numerical integrations.
