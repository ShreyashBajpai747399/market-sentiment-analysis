# Automated Sentiment-Driven Stock Market Analysis System

An end-to-end data pipeline that collects stock market data and financial news, performs sentiment analysis, and generates insights by combining sentiment with time-series stock data.

---

## Project Overview

This project is designed as a **complete ETL (Extract, Transform, Load) pipeline**, focusing on:

- Data ingestion (stock prices + news)
- Data cleaning and processing
- Sentiment analysis on financial news
- Merging structured and unstructured data
- Storing data in a relational database
- Visualizing insights using Power BI

> Note: The primary focus of this project is **data pipeline architecture and workflow design**, not advanced visualization.

---

## Key Features

-  Automated data collection (API + web scraping)
-  Data cleaning and preprocessing using pandas
-  Sentiment analysis using VADER
-  Merging sentiment with stock time-series data
-  Lag-based correlation analysis
-  Structured storage using MySQL
-  Dashboard visualization in Power BI
-  Modular pipeline with logging

---

## Architecture


Data Sources
↓
[Stock API] + [News Scraper]
↓
Raw Data Storage
↓
Data Cleaning & Processing
↓
Sentiment Analysis (VADER)
↓
Data Merging (Time Series + Sentiment)
↓
MySQL Database
↓
Power BI Dashboard


---

## Tech Stack

- **Python** (pandas, NumPy)
- **Web Scraping** (BeautifulSoup)
- **Sentiment Analysis** (VADER)
- **Database** (MySQL)
- **Visualization** (Power BI)

---

##  Project Structure


data/
├── raw/
├── processed/
├── final/

src/
├── ingestion/
├── processing/
├── sentiment/
├── database/

config/
main.py


---

## How to Run

1. Clone the repository:
```bash
git clone https://github.com/ShreyashBajpai747399/market-sentiment-analysis.git
cd market-sentiment-analysis
Install dependencies:
pip install -r requirements.txt
Run the pipeline:
python main.py
📊 Output
Cleaned stock datasets
Sentiment scores for news
Merged dataset (stock + sentiment)
Power BI dashboard for visualization
⚠️ Limitations (Version 1)
No retry logic for failed steps
No orchestration (manual execution)
Basic error handling
Limited scalability
🔄 Future Improvements (Version 2)
Add retry logic and fault tolerance
Introduce pipeline orchestration (e.g., scheduling)
Improve modular architecture
Enhance data validation and logging
Optional: Add predictive modeling