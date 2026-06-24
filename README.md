# Supply Chain Risk Dashboard

A Power BI dashboard tracking supplier performance and supply chain risk for a fictional mid-size German manufacturer. Built to demonstrate how operations teams can move from reactive to proactive risk management using structured KPI monitoring.

---

## Background

During my internship at Spirka Technologies, I built Power BI dashboards for logistics operations — the data was real but I can't share it. So I rebuilt the concept from scratch with synthetic data that mirrors the same structure: supplier deliveries, defect tracking, lead time variance, and order-level risk flags.

The risk scoring model is based on three factors:
1. **On-time delivery rate** — weighted at 50% (biggest operational impact)
2. **Defect rate** — weighted at 25%
3. **Average delay when late** — weighted at 25%

I kept the model simple on purpose. In practice, you'd want to add spend concentration risk and single-source dependency, but those need more data than a synthetic dataset can realistically simulate.

---

## Dashboard Pages

| Page | What it shows |
|---|---|
| Executive Overview | 5 KPI cards + monthly OTD trend + order volume by month |
| Supplier Scorecard | OTD vs defect scatter, risk-colour-coded supplier table |
| Risk Incidents | Drill-through page with flagged orders and disruption causes |
| Spend Analysis | Spend by category, warehouse, and month |

---

## Quick Start

### 1. Install Python dependencies
```bash
pip install pandas matplotlib
```

### 2. Generate the dataset
```bash
python generate_data.py
```

### 3a. Open in Power BI (recommended)
Follow `dashboard_guide.md` — it walks through data loading, DAX measures, and layout step by step.

### 3b. Generate Python charts instead
```bash
python visualize.py
```
Charts are saved to `outputs/`.

---

## Dataset

10 fictional German suppliers across Germany, Poland, and Czech Republic.  
~1,200 order-level rows across 2024.  
Includes realistic variation: bad months, short shipments, defect spikes, seasonal patterns.

No real company data is used anywhere in this project.

---

## Sample Output

### KPI Overview
![KPI Overview](outputs/01_kpi_overview.png)

### Supplier Risk Scorecard
![Supplier Scorecard](outputs/02_supplier_scorecard.png)

### Risk Incidents
![Risk Incidents](outputs/03_risk_incidents.png)

---

## Project Structure

```
supply-chain-risk-dashboard/
├── generate_data.py       # builds all three CSV files
├── visualize.py           # Python chart alternative to Power BI
├── dashboard_guide.md     # step-by-step Power BI build guide
├── data/
│   ├── supply_chain_data.csv
│   ├── supplier_scorecard.csv
│   └── risk_flags.csv
├── outputs/               # generated charts
└── README.md
```

---

## Skills Used
`Power BI` · `DAX` · `Python` · `Pandas` · `Matplotlib` · `Supply Chain Analytics` · `Risk Modelling` · `KPI Design`
