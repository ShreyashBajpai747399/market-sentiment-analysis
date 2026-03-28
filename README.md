# A CORRELATIVE ANALYSIS OF PUBLIC SENTIMENT AND MARKET PERFORMANCE 

## Project Overview

This project builds an automated ETL (Extract, Transform, Load) pipeline that collects stock market data and financial news, performs sentiment analysis using Natural Language Processing (NLP), and stores the processed data in a structured MySQL database for analytical querying and visualization. The system correlates news sentiment scores with stock price movements to uncover relationships between public financial news and market behavior. Final insights are visualized through a Power BI dashboard connected directly to the MySQL database.

---

## Objectives

- To collect historical stock market data (OHLCV) using the yfinance API.
- To collect financial news headlines from Yahoo Finance RSS feeds using web scraping.
- To perform sentiment analysis on news headlines using VADER NLP.
- To clean, validate, and engineer features from raw stock and news data.
- To store all processed data in a normalized MySQL database (star schema, 7 tables).
- To build SQL analytical views for correlation and trend analysis.
- To visualize insights using a Power BI dashboard connected to MySQL.
- To automate the full pipeline end-to-end using a single `main.py` orchestrator.

---

## System Architecture

```
Yahoo Finance (yfinance)          Yahoo Finance RSS Feeds
        │                                  │
        ▼                                  ▼
 Stock Downloader               News Scraper (BeautifulSoup)
        │                                  │
        ▼                                  ▼
   data/raw/stock/                  data/raw/news/
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
              Data Validation
                       │
                       ▼
               Data Cleaning
                       │
                       ▼
           Sentiment Analysis (VADER)
                       │
                       ▼
          Feature Engineering (Moving Avg, RSI)
                       │
                       ▼
          MySQL Database (7 tables, star schema)
                       │
                       ▼
          SQL Analytical Views (4 views)
                       │
                       ▼
            Power BI Dashboard
```

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| pandas | Data processing and transformation |
| NumPy | Numerical operations during feature engineering |
| BeautifulSoup4 | Parsing Yahoo Finance RSS feeds (XML) |
| yfinance | Fetching historical stock market data |
| VADER (vaderSentiment) | Sentiment analysis on news headlines |
| MySQL | Relational database — 7 tables, star schema |
| mysql-connector-python | Python to MySQL connection and loading |
| Power BI | Interactive analytics dashboard |
| GitHub | Version control |

---

## Project Modules

1. **Data Ingestion Module** — Downloads OHLCV stock data and scrapes news headlines from RSS feeds for 5 symbols: AAPL, GOOGL, MSFT, TSLA, AMZN
2. **Data Validation Module** — Checks for nulls, duplicates, out-of-range values, and date gaps before data enters the database
3. **Data Cleaning Module** — Fixes formatting issues, normalizes dates, enforces column schemas
4. **Sentiment Analysis Module** — Scores every news headline using VADER compound score (range: -1.0 to +1.0)
5. **Feature Engineering Module** — Computes daily sentiment aggregates, moving averages, RSI, and price change features
6. **Database Management Module** — Loads all processed data into MySQL using incremental loading (no duplicate inserts)
7. **SQL Analytical Views Module** — 4 pre-built views for sentiment vs price correlation, trend analysis, and aggregated reporting
8. **Power BI Visualization Module** — Dashboard connected directly to MySQL, not CSV files

---

## Stocks Covered

| Symbol | Company |
|---|---|
| AAPL | Apple Inc. |
| GOOGL | Alphabet Inc. (Google) |
| MSFT | Microsoft Corporation |
| TSLA | Tesla Inc. |
| AMZN | Amazon.com Inc. |

---

## Project Structure

```
financial_sentiment_pipeline/
│
├── config.json                        # All settings — DB credentials, paths, symbols
├── main.py                            # Pipeline orchestrator — runs all stages
├── requirements.txt                   # All dependencies
├── .gitignore                         # Excludes data/, logs/, credentials
│
├── data/
│   ├── raw/
│   │   ├── stock/                     # SYMBOL_raw.csv — untouched source data
│   │   └── news/                      # SYMBOL_news_raw.csv — untouched RSS data
│   ├── processed/                     # Cleaned data
│   ├── sentiment/                     # VADER-scored data
│   └── features/                      # Engineered feature data
│
├── src/
│   ├── utils.py                       # Shared: load_config(), setup_logger()
│   ├── ingestion/
│   │   ├── stock_downloader.py        # yfinance downloader
│   │   └── news_scraper.py            # RSS feed scraper
│   ├── validation/
│   │   └── validator.py               # Data quality checks
│   ├── cleaning/
│   │   └── cleaner.py                 # Data cleaning and schema enforcement
│   ├── sentiment/
│   │   └── scorer.py                  # VADER sentiment scoring
│   ├── features/
│   │   ├── aggregator.py              # Daily sentiment aggregation
│   │   └── engineer.py                # Feature engineering (MA, RSI etc.)
│   └── database/
│       └── loader.py                  # MySQL incremental loader
│
├── sql/
│   ├── schema.sql                     # Creates all 7 MySQL tables
│   └── views.sql                      # 4 analytical SQL views
│
└── logs/
    └── pipeline.log                   # Full pipeline execution log
```

---

## Expected Output

- Cleaned and validated stock price data for 5 companies across 2024
- Sentiment-scored news headlines aligned to trading dates
- MySQL database with 7 tables in star schema design
- 4 SQL analytical views for querying sentiment vs price relationships
- Interactive Power BI dashboard showing sentiment trends and price movements
- Complete pipeline execution log at `logs/pipeline.log`

---

## How to Run the Project

**1. Clone the repository**
```bash
git clone https://github.com/your-username/financial_sentiment_pipeline.git
cd financial_sentiment_pipeline
```

**2. Install required libraries**
```bash
pip install -r requirements.txt
```

**3. Configure your settings**

Open `config.json` and update:
```json
"database": {
    "host":     "localhost",
    "port":     3306,
    "name":     "financial_sentiment_db",
    "user":     "root",
    "password": "your_mysql_password_here"
}
```

**4. Create the MySQL database schema**
```bash
mysql -u root -p < sql/schema.sql
```

**5. Run the full pipeline**
```bash
python main.py
```

To run individual stages:
```bash
python src/ingestion/stock_downloader.py
python src/ingestion/news_scraper.py
```

**6. Open Power BI dashboard**

Connect Power BI Desktop to MySQL using the credentials in `config.json` and open the `.pbix` file.

---

## Project Team

| Name | Role |
|---|---|
| Shreyash Bajpai | Data Processing, Feature Engineering, Correlation Analysis, Power BI |
| Khushi Singh | News Data Collection & Sentiment Analysis |
| Kumar Akarsh | Database Management & MySQL Integration |
| Prashant Kumar | Pipeline Automation, Documentation & Deployment |

**Project Guide:** Er. Ravi Krishan Pandey
**Institution:** University of Lucknow, Faculty of Engineering and Technology
**Academic Session:** 2025–2026

---

## Notes

- `data/` and `logs/` folders are excluded from version control via `.gitignore`
- Never commit real database passwords — replace with placeholder before pushing
- The pipeline is designed to be fault-tolerant — if one symbol fails, the rest continue
- All pipeline activity is logged to `logs/pipeline.log` with timestamps and severity levels
