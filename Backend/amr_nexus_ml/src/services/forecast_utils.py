from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
from sklearn.linear_model import LinearRegression
from src.db.models import AMRIsolateRecord
from datetime import datetime

def get_monthly_rates(db: Session, county: str = None, months_back: int = 24):
    query = db.query(
        func.strftime('%Y-%m', AMRIsolateRecord.created_at).label('month'),
        func.avg(AMRIsolateRecord.mdr_flag).label('rate')
    )
    if county:
        query = query.filter(AMRIsolateRecord.county == county)
    query = query.group_by('month').order_by('month').limit(months_back)
    rows = query.all()
    # Convert string month back to datetime for further processing
    return [(datetime.strptime(row.month, '%Y-%m'), float(row.rate)) for row in rows]

def generate_time_series_forecast(db: Session, county: str = None, forecast_months: int = 6):
    monthly = get_monthly_rates(db, county, months_back=24)
    if len(monthly) < 3:
        raise ValueError(f"Insufficient historical data for forecast (county={county})")
    rates = [rate for _, rate in monthly]
    X = np.arange(len(rates)).reshape(-1, 1)
    y = np.array(rates).reshape(-1, 1)
    model = LinearRegression().fit(X, y)
    future_indices = np.arange(len(rates), len(rates) + forecast_months).reshape(-1, 1)
    predictions = model.predict(future_indices).flatten()
    predictions = np.clip(predictions, 0, 1) * 100
    return [{"predicted_mdr_rate": round(float(p), 2)} for p in predictions]
