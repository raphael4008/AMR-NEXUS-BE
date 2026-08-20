import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def generate_mdr_forecast(county: str = None, forecast_months: int = 6):
    from src.db.repositories.trend_repository import get_monthly_mdr_rates
    
    hist_df = get_monthly_mdr_rates(county, months=12)
    
    if hist_df.empty:
        logger.warning(f"No historical data found for county {county}. Using fallback.")
        raise ValueError("Insufficient historical data for forecasting")
    
    hist_df = hist_df.sort_values('month_date')
    first_date = hist_df['month_date'].min()
    hist_df['days'] = (hist_df['month_date'] - first_date).dt.days
    
    X = hist_df[['days']].values
    y = hist_df['mdr_rate'].values * 100
    
    model = LinearRegression()
    model.fit(X, y)
    
    last_date = hist_df['month_date'].max()
    future_dates = [last_date + timedelta(days=30 * (i + 1)) for i in range(forecast_months)]
    future_days = [(d - first_date).days for d in future_dates]
    X_future = np.array(future_days).reshape(-1, 1)
    
    predictions = model.predict(X_future)
    predictions = np.clip(predictions, 0, 100)
    forecast_data = [{"predicted_mdr_rate": round(float(p), 2)} for p in predictions]
    
    return forecast_data