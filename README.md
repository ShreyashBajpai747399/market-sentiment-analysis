# 📈 Automated Sentiment-Driven Stock Market Analysis System

An end-to-end **ETL data pipeline** that ingests live stock prices and financial news, performs sentiment analysis, merges structured and unstructured data, loads everything into MySQL, and visualizes insights through a Power BI dashboard.

> Built to demonstrate real-world data engineering and analytics skills — from raw data ingestion to business-ready insights.

---

## 🔍 What This Project Does

Most stock analysis tools look at price alone. This pipeline goes further — it captures the **sentiment of financial news** around a stock and correlates it with price movement, answering questions like:

- Does negative news actually move TSLA's price the next day?
- Which stocks are most sentiment-sensitive?
- How long does sentiment impact last — T+1, T+2?

---

## 🏗️ Architecture

```
[Yahoo Finance API]    [Yahoo Finance RSS News Scraper]
        ↓                          ↓
   Raw Stock Data             Raw News Articles
        ↓                          ↓
   Data Validation ──────────────────────────
                          ↓
                   Data Cleaning & Processing
                          ↓
              VADER Sentiment Scoring on Headlines
                          ↓
         Merge: Time-Series Stock Data + Sentiment Scores
                          ↓
              Lag-Based Correlation Analysis (T+1, T+2)
                          ↓
                    MySQL Database
                    ↙           ↘
          SQL Views &        Power BI
        Derived Tables       Dashboard
```

---

## ⚙️ Pipeline Steps

The pipeline (`main.py`) orchestrates 8 sequential steps with full logging:

| Step | Script | Description |
|------|--------|-------------|
| 1 | `stock_downloader.py` | Fetches OHLCV data for AAPL, GOOGL, MSFT, TSLA, AMZN |
| 2 | `news_scraper.py` | Scrapes financial headlines via RSS feeds |
| 3 | `validator.py` | Validates schema, nulls, data types |
| 4 | `cleaner.py` | Deduplication, normalization, feature engineering |
| 5 | `scorer.py` | VADER sentiment scoring on headlines |
| 6 | `loader.py` | Incremental load to MySQL (no duplicates) |
| 7 | `populate_derived.sql` | Populates derived/aggregated tables |
| 8 | `views.sql` | Creates analytical SQL views for Power BI |

---

## 📊 Key Insights from the Data

- **TSLA** showed the strongest correlation between negative sentiment and next-day price movement
- Sentiment impact was most pronounced at **T+1 (next day)**, weakening significantly by T+2
- **AAPL and MSFT** showed higher price stability despite negative news — suggesting stronger investor confidence
- Lag-based correlation analysis revealed sentiment score below -0.3 consistently preceded downward price pressure

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.x |
| Data Processing | pandas, NumPy |
| Web Scraping | BeautifulSoup, feedparser |
| Sentiment Analysis | VADER (vaderSentiment) |
| Database | MySQL |
| Orchestration | Custom Python pipeline runner |
| Logging | Python logging module |
| Visualization | Power BI |

---

## 📁 Project Structure

```
market-sentiment-analysis/
├── main.py                  # Pipeline orchestrator
├── config.json              # DB credentials & path config
├── requirements.txt
├── src/
│   ├── ingestion/
│   │   ├── stock_downloader.py
│   │   └── news_scraper.py
│   ├── validation/
│   │   └── validator.py
│   ├── cleaning/
│   │   └── cleaner.py
│   ├── sentiment/
│   │   └── scorer.py
│   ├── database/
│   │   └── loader.py
│   └── utils.py
├── sql/
│   ├── populate_derived.sql
│   └── views.sql
└── logs/                    # Auto-generated pipeline logs
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- MySQL Server running locally or remotely
- Power BI Desktop (for dashboard)

### 1. Clone the repository
```bash
git clone https://github.com/ShreyashBajpai747399/market-sentiment-analysis.git
cd market-sentiment-analysis
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure database connection
Edit `config.json` with your MySQL credentials:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "your_username",
    "password": "your_password",
    "name": "market_sentiment"
  },
  "paths": {
    "logs": "logs/"
  }
}
```

### 4. Run the full pipeline
```bash
python main.py
```

Pipeline logs are saved automatically to `/logs/pipeline_YYYY-MM-DD_HH-MM-SS.log`

---

## 📤 Pipeline Output

Each run produces:
- ✅ Cleaned stock price datasets (OHLCV)
- ✅ Sentiment-scored news articles
- ✅ Merged dataset (price + sentiment + lag features)
- ✅ Populated MySQL derived tables and analytical views
- ✅ Timestamped log file for full run audit

---

## ⚠️ Known Limitations (v1)

- Manual execution only — no scheduler yet
- No retry logic for failed individual steps
- Basic error handling (exits on first failure)
- MySQL credentials stored in config.json (not env variables)

---

## 🔮 Planned Improvements (v2)

- [ ] Add Apache Airflow for pipeline scheduling
- [ ] Move credentials to `.env` file (python-dotenv)
- [ ] Add retry logic with exponential backoff
- [ ] Add data quality checks with Great Expectations
- [ ] Add predictive modeling layer (price direction classification)
- [ ] Dockerize the pipeline

---

## 🤝 Connect

**Shreyash Bajpai**
- 📧 [your email here]
- 💼 [LinkedIn URL here]
- 🐙 [GitHub Profile](https://github.com/ShreyashBajpai747399)