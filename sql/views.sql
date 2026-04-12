use market_sentiment_analysis;

drop view if exists view_sentiment_vs_stock_price;
drop view if exists view_moving_averages;
drop view if exists view_rsi_analysis;
drop view if exists view_lag_correlation;



create view view_sentiment_vs_stock_price as (
	
select 
		sym.symbol Symbol ,
		sym.company_name Company_Name,
        
        d.full_date Date,
        d.day_of_week Day_of_Week ,
        d.is_Trading_Day is_Trading_Day,
        
        f.close Close,
        
        t.daily_return Daily_Return,
        
        s.avg_sentiment Average_Sentiment,
        coalesce(s.article_count,0) Article_Count,
        coalesce(s.Positive_count,0) Positive_Count,
        coalesce(s.Negative_count,0) Negative_Count,
        coalesce(s.Neutral_count,0) Neutral_Count,
        
        case 
			WHEN t.daily_return is NULL then "NO DATA"
			when t.daily_return > 0 then "UP"
            when t.daily_return < 0 then "DOWN"
            else "FLAT"
		end as Price_Direction,
        
        case 
			when s.avg_sentiment is NULL then "NO DATA"
			when s.avg_sentiment > 0.30 then "POSITIVE"
            when s.avg_sentiment < -0.30 then "NEGATIVE"
            else "NEUTRAL"
		end Daily_Sentiment_Label
    from Fact_Stock_Prices f
    join dim_symbol sym
    on sym.symbol_id=f.symbol_id
    join dim_date d
    on d.date_id=f.date_id
    left join Fact_Sentiment_Daily s
    on f.date_id=s.date_id and
    f.symbol_id=s.symbol_id
    left join Fact_Technical_Features t
    on f.date_id=t.date_id and
    f.symbol_id=t.symbol_id
);

create view view_moving_averages as (
	select 
		sym.symbol as Symbol,
        sym.company_name as Company_Name,
        
		d.full_date as Date,
        
        f.close as Close,
        
        t.ma_7 as Ma_7,
        t.ma_14 as Ma_14,
        t.ma_30 as Ma_30,
        
        case 
        when f.close>t.ma_7 then "ABOVE"
		when f.close<t.ma_7 then "BELOW"
        else "AT"
        end as Price_Vs_Ma_7,
        
        case 
        when f.close>t.ma_14 then "ABOVE"
		when f.close<t.ma_14 then "BELOW"
        else "AT"
        end as Price_Vs_Ma_14,
        
        case 
			when f.close>t.ma_30 then "ABOVE"
            when f.close < t.ma_30 then "BELOW"
			else "AT"
		end as Price_Vs_Ma_30,
        
        round(
			(f.close-t.ma_7)/NULLIF(t.ma_7,0) * 100
        ,2	) as Pct_From_ma_7
        
    from Fact_Technical_Features t
	join dim_symbol sym
    on sym.symbol_id=t.symbol_id
    join dim_date d
    on d.date_id=t.date_id
    left join fact_stock_prices f
    on f.date_id=t.date_id
    and f.symbol_id=t.symbol_id
);

create view  view_rsi_analysis as (
	select 
		sym.symbol Symbol,
		sym.company_name Company_Name ,
        d.full_date Date ,
        f.close Close,
		t.rsi_14 Rsi,
        t.daily_return Daily_Return,
        t.price_volatility Price_Volatility,
        
        case
			when t.rsi_14>=70 then "OVERBOUGHT"
            when t.rsi_14<=30 then "OVERSOLD"
            when t.rsi_14 is NULL then "NO DATA"
            else "NEUTRAL"
		end as rsi_signal,
        case 
			when t.rsi_14 is NULL then "NO DATA"
			when t.rsi_14>=70 and s.avg_sentiment<=-0.30 then "BEARISH DIVERGENCE"
            when t.rsi_14<=30 and s.avg_sentiment>=0.30 then "BULLISH DIVERGENCE"
            else "NO SIGNAL"
		end as combined_signal
    from fact_stock_prices f
	join dim_symbol sym
    on sym.symbol_id=f.symbol_id
    join dim_date d
    on d.date_id=f.date_id
	left join Fact_Technical_Features t 
    on f.symbol_id=t.symbol_id
    and f.date_id=t.date_id
    left join fact_sentiment_daily s
    on f.symbol_id=s.symbol_id
    and f.date_id=s.date_id
);

create view view_lag_correlation as (
	with lag_cte as(
		select 
        f.date_id , 
        f.symbol_id ,
        lag(avg_sentiment,1) over(partition by f.symbol_id order by d.full_date) lag_sentiment 
        from Fact_Sentiment_Daily f
        left join dim_date d
        on d.date_id=f.date_id
        )
	select 
    sym.symbol Symbol , 
    sym.company_name Company_Name,
    d.full_date Date,
    f.close Close,
    t.daily_return Daily_Return,
    
    s.avg_sentiment Average_Sentiment,
    
    ctel.lag_sentiment Yesterday_Sentiment,
    
    case 
		when ctel.lag_sentiment is NULL then "NO DATA"
		when ctel.lag_sentiment >=0.30 then "POSITIVE"
        when ctel.lag_sentiment <=-0.30 then "NEGATIVE"	
        else "NEUTRAL"
	end Yesterday_Sentiment_Label,
    
    case 
		when ctel.lag_sentiment is NULL or t.daily_return is NULL then "NO DATA"
		when ctel.lag_sentiment >=0.30 and t.daily_return>0 then "AGREEMENT"
        when ctel.lag_sentiment <=-0.30 and t.daily_return<0 then "AGREEMENT"
        else "DISAGREEMENT"
	end Lag_Signal
    
    from fact_stock_prices f
    join dim_date d 
    on d.date_id=f.date_id
    join dim_symbol sym
    on sym.symbol_id=f.symbol_id
    left join fact_technical_features t 
    on t.date_id=f.date_id 
    and t.symbol_id=f.symbol_id
    left join fact_sentiment_daily s 
    on s.date_id=f.date_id
    and s.symbol_id=f.symbol_id
    left join lag_cte ctel
    on ctel.date_id=f.date_id
    and ctel.symbol_id=f.symbol_id
);