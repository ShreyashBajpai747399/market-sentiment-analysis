create database if not exists market_sentiment_analysis
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

use market_sentiment_analysis;

create table if not exists DIM_SYMBOL (
	symbol_id int not null auto_increment,
    symbol varchar(10) not null,
    company_name varchar(50) not null,
	primary key (symbol_id),
    unique key uq_symbol(symbol)
);

create table if not exists DIM_DATE(
	date_id int not null auto_increment,
    full_date date not null ,
    year int not null,
    month int not null,
    day int not null,
    day_of_week varchar(10) not null,
    is_trading_day boolean not null default False,
    
    primary key(date_id),
    unique key uq_full_date(full_date)
);

create table if not exists Fact_Stock_Prices (
	price_id int not null auto_increment ,
    symbol_id int not null,
    date_id int not null,
    open decimal(10,4) not null,
    high decimal(10,4) not null,
    low decimal(10,4) not null,
    close decimal(10,4) not null,
    volume bigint not null,
    primary key (price_id),
    unique key uq_stock(symbol_id,date_id),
    foreign key (date_id) references DIM_DATE(date_id),
    foreign key (symbol_id) references DIM_SYMBOL(symbol_id)
);

create table if not exists Fack_News_Articles(
	article_id int not null auto_increment,
    date_id int not null,
    symbol_id int not null,
    title varchar(500) not null,
    link varchar(1000) not null,
    compound_score decimal(5,4) not null,
    positive_score decimal(5,4) not null,
    negative_score decimal(5,4) not null,
    neutral_score decimal(5,4) not null,
    sentiment_label varchar(50) not null,
    
    primary key (article_id),
    unique key uq_news(link(255)),
    
    foreign key (symbol_id) references DIM_SYMBOL(symbol_id),
    foreign key (date_id) references DIM_DATE(date_id)
);

create table if not exists Fact_Sentiment_Daily(
	sentiment_id int not null auto_increment,
	date_id int not null,
    symbol_id int not null,
    avg_sentiment decimal(5,4) not null,
    article_count int not null,
	positive_count int not null,
    negative_count int not null,
    neutral_count int not null,
    
    primary key (sentiment_id),
    unique key uq_sentiment_daily(symbol_id,date_id),
    
    foreign key (symbol_id) references DIM_SYMBOL(symbol_id),
    foreign key (date_id) references DIM_DATE(date_id)
);

create table if not exists Fact_Technical_Features(
	feature_id int not null auto_increment,
    symbol_id int not null,
    date_id int not null,
    ma_7 decimal(10,4) not null,
    ma_14 decimal(10,4) not null,
    ma_30 decimal(10,4) not null,
    rsi_14 decimal(5,2) not null,
    daily_return decimal(8,4) not null,
    price_volatility decimal(8,4) not null,
    
    primary key (feature_id),
    unique key uq_technical(symbol_id,date_id),
    
	foreign key (symbol_id) references DIM_SYMBOL(symbol_id),
    foreign key (date_id) references DIM_DATE(date_id)
);

create table if not exists Fact_Combined_Analysis(
	analysis_id int not null auto_increment,
    symbol_id int not null,
    date_id int not null,
    close decimal(10,4) not null,
    avg_sentiment decimal(10,4) not null, 
    rsi_14 decimal(5,2) not null, 
    ma_7 decimal(10,4) not null,
    sentiment_label varchar(50) not null,
    
    primary key (analysis_id),
    unique key uq_analysis(symbol_id,date_id),
    
	foreign key (symbol_id) references DIM_SYMBOL(symbol_id),
    foreign key (date_id) references DIM_DATE(date_id)
);