# 📈 Market Sentiment Analysis — Automated ETL Pipeline

> An end-to-end data pipeline that ingests live stock prices and financial news, scores sentiment using NLP, merges structured and unstructured data, loads everything into MySQL, and surfaces business insights through a Power BI dashboard.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Database-orange?logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-yellow?logo=powerbi&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 🧠 The Business Problem

Most stock market tools track price — but price moves on *information*. This pipeline asks:

- Does negative news actually cause TSLA's price to drop the next day?
- Which stocks are most sensitive to media sentiment?
- How long does sentiment impact persist — T+1? T+2?

By combining financial news sentiment with time-series price data, this project turns raw market noise into actionable insights.

---

## 🏗️ Pipeline Architecture

```
┌─────────────────────┐     ┌──────────────────────────┐
│   Yahoo Finance API  │     │  Yahoo Finance RSS Feeds  │
│  (OHLCV Stock Data) │     │    (Financial Headlines)  │
└────────┬────────────┘     └────────────┬─────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────────┐
│              Data Validation Layer                   │
│         (Schema checks · Null handling)             │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│              Data Cleaning & Processing              │
│      (Deduplication · Normalisation · Features)     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│           VADER Sentiment Scoring (NLP)              │
│     (Compound score per headline per stock)          │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│         Merge: Price Time-Series + Sentiment         │
│          Lag Analysis: T+1, T+2 Correlation          │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    MySQL    │
                    │  Database   │
                    └──────┬──────┘
                    ┌──────┴──────┐
                    ▼             ▼
             SQL Views &     Power BI
           Derived Tables    Dashboard
```

---

## ⚙️ Pipeline Steps

Orchestrated by `main.py` — runs 8 sequential steps with full timestamped logging:

| # | Step | Script | What it does |
|---|------|--------|--------------|
| 1 | Stock Ingestion | `src/ingestion/stock_downloader.py` | Fetches OHLCV data for AAPL, GOOGL, MSFT, TSLA, AMZN |
| 2 | News Ingestion | `src/ingestion/news_scraper.py` | Scrapes financial headlines via RSS |
| 3 | Validation | `src/validation/validator.py` | Schema checks, null handling, type validation |
| 4 | Cleaning | `src/cleaning/cleaner.py` | Deduplication, normalisation, feature engineering |
| 5 | Sentiment Scoring | `src/sentiment/scorer.py` | VADER compound score per headline |
| 6 | Database Load | `src/database/loader.py` | Incremental load to MySQL (deduplication-safe) |
| 7 | Derived Tables | `sql/populate_derived.sql` | Populates aggregated/analytical tables |
| 8 | Views | `sql/views.sql` | Creates analytical views consumed by Power BI |

---

## 📊 Key Findings

- **TSLA** showed the strongest correlation between negative sentiment and next-day price decline
- Sentiment impact peaked at **T+1 (next trading day)** and weakened significantly by T+2
- **AAPL and MSFT** demonstrated higher price stability despite negative news — indicating stronger investor confidence buffers
- Sentiment scores below **-0.3 compound** consistently preceded downward price pressure across all 5 stocks

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ |
| Data Processing | pandas, NumPy |
| Web Scraping | BeautifulSoup4, feedparser |
| NLP / Sentiment | VADER (vaderSentiment) |
| Database | MySQL |
| Pipeline Orchestration | Custom Python runner (subprocess) |
| Logging | Python logging module |
| Visualisation | Power BI |

---

## 📁 Project Structure

```
market-sentiment-analysis/
│
├── main.py                        # Pipeline orchestrator — runs all 8 steps
├── config.json                    # DB config & path settings (use template below)
├── requirements.txt               # Python dependencies
│
├── src/
│   ├── ingestion/
│   │   ├── stock_downloader.py    # Yahoo Finance API → raw stock data
│   │   └── news_scraper.py        # RSS scraper → raw news headlines
│   ├── validation/
│   │   └── validator.py           # Schema + data quality checks
│   ├── cleaning/
│   │   └── cleaner.py             # Cleaning, dedup, feature engineering
│   ├── sentiment/
│   │   └── scorer.py              # VADER sentiment scoring
│   ├── database/
│   │   └── loader.py              # Incremental MySQL loader
│   └── utils.py                   # Shared utilities (logger, config loader)
│
├── sql/
│   ├── populate_derived.sql       # Aggregated table population
│   └── views.sql                  # Analytical views for Power BI
│
└── logs/                          # Auto-generated pipeline run logs
    └── pipeline_YYYY-MM-DD_HH-MM-SS.log
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MySQL Server (local or remote)
- Power BI Desktop (for dashboard)

### 1. Clone the repo
```bash
git clone https://github.com/ShreyashBajpai747399/market-sentiment-analysis.git
cd market-sentiment-analysis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure database connection
Create a `config.json` in the root directory using this template:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "your_mysql_username",
    "password": "your_mysql_password",
    "name": "market_sentiment"
  },
  "paths": {
    "logs": "logs/"
  }
}
```
> ⚠️ Never commit real credentials. Add `config.json` to `.gitignore`.

### 4. Run the pipeline
```bash
python main.py
```

Each run generates a timestamped log at `logs/pipeline_YYYY-MM-DD_HH-MM-SS.log`

---

## 📤 Pipeline Output

A successful run produces:

- ✅ Cleaned OHLCV stock datasets (5 stocks)
- ✅ Sentiment-scored news headlines with compound scores
- ✅ Merged dataset — price + sentiment + lag features (T+1, T+2)
- ✅ Populated MySQL derived tables and analytical views
- ✅ Full audit log of the pipeline run

---

## ⚠️ Known Limitations

- Manual execution only — no scheduler yet
- Pipeline exits on first failure (no retry logic)
- Credentials via config.json (not environment variables)
- Single-threaded ingestion — slower on large date ranges

---

## 🔮 Planned Improvements

- [ ] Apache Airflow integration for scheduling
- [ ] Migrate credentials to `.env` + `python-dotenv`
- [ ] Step-level retry logic with exponential backoff
- [ ] Data quality checks using Great Expectations
- [ ] Predictive modelling — next-day price direction classifier
- [ ] Docker containerisation

---

## 👤 Author

**Shreyash Bajpai**
- 💼 [LinkedIn](www.linkedin.com/in/shreyashbajpaiii)
- 🐙 [GitHub](https://github.com/ShreyashBajpai747399)
- 📧 shreyashbajpai0@gmail.com