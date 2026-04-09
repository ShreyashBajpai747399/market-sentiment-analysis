-- populate derived data 

use market_sentiment_analysis;

insert ignore into Fact_Sentiment_Daily(
	date_id,
    symbol_id ,
    avg_sentiment,
    article_count ,
	positive_count,
    negative_count,
    neutral_count)
select
    date_id,
    symbol_id,
	round(AVG(compound_score) ,4) as avg_sentiment,
    count(*) as article_count,
    sum(sentiment_label="POSITIVE") as positive_count,
    sum(sentiment_label="NEGATIVE") as negative_count,
    sum(sentiment_label="NEUTRAL") as neutral_count
from Fact_News_Articles
group by symbol_id,date_id ;

SELECT CONCAT('fact_sentiment_daily — ', ROW_COUNT(), ' rows inserted') AS status;

insert ignore into Fact_Technical_Features(
    symbol_id ,
    date_id ,
    ma_7 ,
    ma_14 ,
    ma_30,
    rsi_14,
    daily_return ,
    price_volatility)
with stock_with_dates as (
	select 
		f.symbol_id,
		f.date_id,
		d.full_date,
		f.close,
		f.high,
		f.low
	from Fact_Stock_Prices f
	left join dim_date d
	on f.date_id=d.date_id
),
-- daily return = (today close - yesterday close) / yesterday close * 100
	with_return as(
		select 
			symbol_id,
			date_id,
			full_date,
			close,
			high,
			low,
			round(
				((close-lag(close) over(partition by symbol_id order by date_id))
					/ NULLIF (lag(close) over(partition by symbol_id order by date_id),0)) * 100
			,4) as daily_return
		from stock_with_dates
	),

	with_ma as (
		select 
			symbol_id,
			date_id,
			full_date,
			close,
			high,
			low,
			daily_return,
			round(
				(avg(close) over (partition by symbol_id order by date_id rows between 6 preceding and current row))
			,4) as ma_7,
			
			round(
				(avg(close) over (partition by symbol_id order by date_id rows between 13 preceding and current row))
			,4) as ma_14 ,
			
			round(
				(avg(close) over (partition by symbol_id order by date_id rows between 29 preceding and current row))
			,4) as ma_30
		from with_return 
	),

	with_rsi as (
		select 
			symbol_id,
			date_id,
			ma_7,
			ma_14,
			ma_30,
			daily_return,
			round((high-low),4) as price_volatility,
			avg(case when daily_return>0 
				then daily_return 
				else 0 
				end)
			over(partition by symbol_id order by date_id rows between 13 preceding and current row) as avg_gain,
			
			avg(case when daily_return<0
				then abs(daily_return)
				else 0
				end)
			over(partition by symbol_id order by date_id rows between 13 preceding and current row) as avg_loss
		from with_ma
	)

SELECT
	symbol_id ,
    date_id,
    ma_7,
    ma_14,
    ma_30,
    round(
		case when avg_loss =  0 then 100
        else 100-(100/(1+avg_gain/avg_loss))
        end ,4) as rsi_14,
    daily_return,
    price_volatility
from  with_rsi;
    

select concat('Fact_Technical_Features — ', row_count() ,'rows inserted') as status ;

insert ignore into Fact_Combined_Analysis(
	symbol_id ,
    date_id ,
    close ,
    avg_sentiment , 
    rsi_14 , 
    ma_7 ,
    sentiment_label
    )
select 
	f.symbol_id ,
    f.date_id ,
    f.close ,
    s.avg_sentiment , 
    t.rsi_14 , 
    t.ma_7 ,
    n.sentiment_label
from fact_stock_prices f
left join Fact_Sentiment_Daily s
on f.symbol_id=s.symbol_id
and f.date_id=s.date_id
left join Fact_Technical_Features t 
on t.symbol_id=f.symbol_id
and t.date_id=f.date_id
left join (
	select 
		date_id,
        symbol_id,
        case when sum(sentiment_label="POSITIVE") >= greatest(sum(sentiment_label="NEGATIVE"),sum(sentiment_label="NEUTRAL")) then "POSITIVE"
			when sum(sentiment_label="NEGATIVE")>= sum(sentiment_label="NEUTRAL") then "NEGATIVE"
            else "NEUTRAL"
		end as sentiment_label
	from fact_news_articles
    group by date_id , symbol_id
	) n
on n.symbol_id=f.symbol_id
and n.date_id=f.date_id;