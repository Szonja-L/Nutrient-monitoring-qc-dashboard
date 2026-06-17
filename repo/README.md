# Nutrient Monitoring & QC Dashboard — Case Study

A case study from a data analytics internship in the food/nutrition
manufacturing sector, redesigning a manual, Excel-based quality-control
process into an automated, statistically-grounded Power BI dashboard.

**📄 Full write-up: [`CASE_STUDY.md`](CASE_STUDY.md)**

> **A note on data and confidentiality.** The original project was built on
> proprietary, real-world specification and lab data belonging to the host
> company. No real data, specification values, internal system names, or
> company identifiers appear anywhere in this repository. All numbers and
> visuals here are synthetic and for illustration only. See the disclosure
> note at the top of `CASE_STUDY.md` for details.

## Repository structure

```
.
├── CASE_STUDY.md                          # Full case study: problem, approach, methods, results
├── visuals/                                # Mock dashboard visuals (synthetic data)
│   ├── 01_summary_statistics.png
│   ├── 02_scatter_outlier_view.png
│   ├── 03_seasonality_view.png
│   └── 04_predictive_trends_view.png
└── code/
    ├── generate_mock_visuals.py            # Generates the mock visuals from synthetic data
    └── dax_and_powerquery_reference.md     # Generalized DAX measures & Power Query (M) patterns
```

## What this project demonstrates

- **Data harmonization**: reconciling two real-world datasets with inconsistent
  naming conventions and units of measurement.
- **Data modelling**: star-schema design for fast, scalable filtering and
  aggregation in a BI tool.
- **Statistical quality control**: RSD%, recovery %, deviation %, and both
  standard and modified Z-score outlier detection (robust to skewed data).
- **Time-series exploration**: rolling averages, month-over-month change, and
  regression-based trend analysis, including an honest discussion of where
  the regression approach fell short (low R² values).
- **Dashboard/UX design**: translating a statistical pipeline into a
  self-service tool for non-technical stakeholders.
- **Clear communication of limitations**: a core part of doing analytics
  responsibly is being explicit about where a model or pipeline doesn't work
  well, not just where it does.

## Reproducing the mock visuals

```bash
pip install numpy pandas matplotlib
python code/generate_mock_visuals.py
```

This regenerates the four PNGs in `visuals/` from fully synthetic data — no
external files or credentials required.

## Related work

This project pairs well with my [differential gene expression analysis
portfolio project](#) (transcriptomics/bioinformatics), which applies a
similar mindset — turning a domain-specific, statistically grounded analysis
into a clear, reproducible, end-to-end pipeline — in a different scientific
context.
