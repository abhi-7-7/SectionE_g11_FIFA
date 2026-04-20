# FIFA World Cup Analytics — SectionE Group 11

**Newton School of Technology | DVA Capstone 2**
**Sector:** Sports & Entertainment Analytics
**Team ID:** SectionE_g11

---

## Business Problem

Which factors — home advantage, match stage, team historical performance, and player deployment — most significantly predict match outcomes at the FIFA World Cup? How can national football federations use these insights to optimize squad selection and tournament strategy?

---

## Dataset

| File | Rows | Columns | Description |
|------|------|---------|-------------|
| WorldCupPlayers.csv | 37,784 | 9 | Player-level match data (1930–2014) |
| WorldCupMatches.csv | 4,572 | 20 | Match-level data with scores, attendance, referees |
| WorldCups.csv | 20 | 10 | Tournament-level summary per edition |

**Primary analytical dataset:** `data/processed/wc_master.csv` — a merged, cleaned dataset combining all three sources (37,784 rows × 22+ columns), created by the ETL pipeline.

**Source:** [Kaggle — FIFA World Cup](https://www.kaggle.com/datasets/abecklas/fifa-world-cup)

---

## KPI Framework

| KPI | Description |
|-----|-------------|
| Win Rate by Team | Wins / Total matches played per team |
| Goals per Match | Average total goals per match per tournament year |
| Home Advantage Index | Win rate of host nation vs. overall win rate |
| Knockout Qualification Rate | % of group stage teams reaching knockout rounds |
| Attendance Growth Rate | YoY attendance change across tournaments |
| Player Goal Contribution | Goals scored per player per tournament |
| Stage Difficulty Index | Average goals scored by stage (Group → Final) |
| Team Consistency Score | Number of tournaments a team appeared in |

---

## Repository Structure

```
SectionE_g11_FIFA/
├── README.md
├── data/
│   ├── raw/                    ← Original datasets (never edited)
│   └── processed/              ← Cleaned output from ETL pipeline
├── notebooks/
│   ├── 01_extraction.ipynb     ← Load & inspect raw data
│   ├── 02_cleaning.ipynb       ← ETL cleaning pipeline
│   ├── 03_eda.ipynb            ← Exploratory data analysis
│   ├── 04_statistical_analysis.ipynb ← Correlation, regression, hypothesis testing
│   └── 05_final_load_prep.ipynb      ← KPI computation & Tableau export
├── scripts/
│   └── etl_pipeline.py         ← Standalone ETL script
├── tableau/
│   ├── screenshots/            ← Dashboard screenshots
│   └── dashboard_links.md      ← Tableau Public URL
├── reports/
│   ├── project_report.pdf
│   └── presentation.pdf
└── docs/
    └── data_dictionary.md
```

---

## Team Members & Roles

| Role | Member |
|------|--------|
| Project Lead | |
| Data Lead | |
| ETL Lead | |
| Analysis Lead | |
| Visualization Lead | |
| Strategy Lead | |
| PPT & Quality Lead | |

---

## How to Run

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter

# Run notebooks in order
jupyter notebook notebooks/01_extraction.ipynb
jupyter notebook notebooks/02_cleaning.ipynb
jupyter notebook notebooks/03_eda.ipynb
jupyter notebook notebooks/04_statistical_analysis.ipynb
jupyter notebook notebooks/05_final_load_prep.ipynb

# Or run the standalone ETL pipeline
python scripts/etl_pipeline.py
```

---

## Key Insights (Summary)

See `reports/project_report.pdf` for full analysis. Dashboard: see `tableau/dashboard_links.md`.
