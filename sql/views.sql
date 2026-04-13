use market_sentiment_analysis;

drop view if exists view_sentiment_vs_stock_price;
drop view if exists view_moving_averages;
drop view if exists view_rsi_analysis;
drop view if exists view_lag_correlation;
drop view if exists view_correlation_analysis;



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
			WHEN t.daily_return is NULL then 'NO DATA'
			when t.daily_return > 0 then 'UP'
            when t.daily_return < 0 then 'DOWN'
            else 'FLAT'
		end as Price_Direction,
        
        case 
			when s.avg_sentiment is NULL then 'NO DATA'
			when s.avg_sentiment > 0.30 then 'POSITIVE'
            when s.avg_sentiment < -0.30 then 'NEGATIVE'
            else 'NEUTRAL'
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
        when f.close>t.ma_7 then 'ABOVE'
		when f.close<t.ma_7 then 'BELOW'
        else 'AT'
        end as Price_Vs_Ma_7,
        
        case 
        when f.close>t.ma_14 then 'ABOVE'
		when f.close<t.ma_14 then 'BELOW'
        else 'AT'
        end as Price_Vs_Ma_14,
        
        case 
			when f.close>t.ma_30 then 'ABOVE'
            when f.close < t.ma_30 then 'BELOW'
			else 'AT'
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
			when t.rsi_14>=70 then 'OVERBOUGHT'
            when t.rsi_14<=30 then 'OVERSOLD'
            when t.rsi_14 is NULL then 'NO DATA'
            else 'NEUTRAL'
		end as rsi_signal,
        case 
			when t.rsi_14 is NULL then 'NO DATA'
			when t.rsi_14>=70 and s.avg_sentiment<=-0.30 then 'BEARISH DIVERGENCE'
            when t.rsi_14<=30 and s.avg_sentiment>=0.30 then 'BULLISH DIVERGENCE'
            else 'NO SIGNAL'
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
		when ctel.lag_sentiment is NULL then 'NO DATA'
		when ctel.lag_sentiment >=0.30 then 'POSITIVE'
        when ctel.lag_sentiment <=-0.30 then 'NEGATIVE'	
        else 'NEUTRAL'
	end Yesterday_Sentiment_Label,
    
    case 
		when ctel.lag_sentiment is NULL or t.daily_return is NULL then 'NO DATA'
		when ctel.lag_sentiment >=0.30 and t.daily_return>0 then 'AGREEMENT'
        when ctel.lag_sentiment <=-0.30 and t.daily_return<0 then 'AGREEMENT'
        else 'DISAGREEMENT'
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

create view view_correlation_analysis as(
	
	with base as (
		select 
        sym.symbol_id as symbol_id,
		sym.symbol as Symbol,
		sym.company_name as Company_Name,
        d.date_id as date_id,
        d.full_date as Date,
		s.avg_sentiment as X,
		t.daily_return as Y,
        lag(avg_sentiment,1) over (partition by sym.symbol order by d.full_date) as X_lag
		from fact_sentiment_daily as s
		left join fact_technical_features as t
		on t.date_id=s.date_id
		and t.symbol_id=s.symbol_id
		join dim_symbol as sym 
		on sym.symbol_id=s.symbol_id
        join dim_date as d
        on d.date_id=s.date_id
        where t.daily_return is not NULL
		),
	stats as(
		select 
			Symbol,
            symbol_id,
			Company_Name,
			count(*) as n,
			sum(X) as Sum_X,
			sum(Y) as sum_Y,
			sum(X*Y) as sum_XY,
			sum(X*X) as sum_XX,
			sum(Y*Y) as sum_YY,
			round(avg(X),4) as Avg_X,
			round(avg(Y),4) as Avg_Y
		from base
        group by symbol_id,symbol,company_name
		),
	lag_stats as (
		select 
			symbol_id,
			Symbol,
            company_name,
			count(X_lag) as lag_n,
            sum(X_lag) as lag_sum_X,
			sum(Y) as sum_Y,
			sum(Y*Y) as sum_YY,
            sum(X_lag*Y) as lag_sum_XY,
            sum(X_lag*X_lag) as lag_sum_XX,
            round(avg(X_lag),4) as lag_avg_X,
			round(avg(Y),4) as Avg_Y
		from base 
        where X_lag is not NULL
        group by symbol_id,symbol,company_name
    ),
	coerr as (
		select 
			Symbol,
            symbol_id,
			Company_Name,
			Avg_X avg_sentiment,
			Avg_Y avg_return,
			round(
				((n * sum_XY) - (sum_X * sum_Y))/
					NULLIF(SQRT((n * sum_XX - sum_X * sum_X) * (n * sum_YY - sum_Y * sum_Y))
				,0)
			,4) as pearson_correlation 
		from stats
        where n>2
		),
	lag_coerr as(
		select 
        Symbol,
        symbol_id,
		Company_Name,
        lag_avg_X lag_avg_X,
        avg_y avg_return,
        
        round(
			((lag_n * lag_sum_XY) - lag_sum_X * sum_Y) /
				NULLIF((SQRT((lag_n * lag_sum_XX - lag_sum_X * lag_sum_X ) * (lag_n * sum_YY - sum_Y * sum_Y))),0)
        ,4) as lag_pearson_correlation
        from lag_stats
        where lag_n>2
    )
    select 
		st.Symbol,
        st.Company_Name,
        st.Avg_X as Average_Sentiment,
        lpc.lag_avg_X as Average_Lag_Sentiment,
        st.Avg_Y as Average_Return,
        pc.Pearson_Correlation as Same_Day_Pearson_Correlation,
        
        case 
			when pc.pearson_correlation>=0.5 then 'STRONG POSITIVE'
            when pc.pearson_correlation>=0.2 then 'WEAK POSITIVE'
            when pc.pearson_correlation<=-0.5 then 'STRONG NEGATIVE'
            when pc.pearson_correlation<=-0.2 then 'WEAK NEGATIVE'
            else 'NO CORRELATION'
		end as Same_Day_Correlation_Strength,
        
        Lag_Pearson_Correlation,
        case 
			when lpc.Lag_Pearson_Correlation>=0.5 then 'STRONG POSITIVE'
            when lpc.Lag_Pearson_Correlation>=0.2 then 'WEAK POSITIVE'
            when lpc.Lag_Pearson_Correlation<=-0.5 then 'STRONG NEGATIVE'
            when lpc.Lag_Pearson_Correlation<=-0.2 then 'WEAK NEGATIVE'
            else 'NO CORRELATION'
		end as lag_correlation_strength
        
	from stats as st
    join coerr as pc
    on pc.symbol_id=st.symbol_id
    left join lag_coerr lpc
    on lpc.symbol_id=st.symbol_id
    
);