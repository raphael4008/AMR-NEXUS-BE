from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
from src.api.deps import get_db
from src.db.models import AMRIsolateRecord
from src.utils.logger import logger

print("✅ ews_router is being imported!")

ews_router = APIRouter()

_cache = {}
CACHE_TTL = 3600


def get_monthly_rates(db: Session, county: str = None, months_back: int = 24):
    query = db.query(
        func.date_trunc('month', AMRIsolateRecord.created_at).label('month'),
        func.avg(AMRIsolateRecord.mdr_flag).label('rate')
    )
    if county:
        query = query.filter(AMRIsolateRecord.county == county)
    query = query.group_by('month').order_by('month').limit(months_back)
    rows = query.all()
    return [(row.month, float(row.rate)) for row in rows]


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


@ews_router.get("/forecast")
async def get_ews_forecast(
    county: str = Query(None, description="Optional county filter"),
    db: Session = Depends(get_db)
):
    cache_key = f"forecast_{county or 'all'}"
    now = datetime.now().timestamp()
    if cache_key in _cache and (now - _cache[cache_key]['timestamp']) < CACHE_TTL:
        logger.info(f"Returning cached forecast for {cache_key}")
        return _cache[cache_key]['data']

    try:
        forecast = generate_time_series_forecast(db, county)
        _cache[cache_key] = {"timestamp": now, "data": forecast}
        return forecast
    except ValueError as e:
        logger.warning(f"Forecast failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /ews/forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# -------- DEBUG ROUTE --------
@ews_router.get("/ping")
async def ping():
    return {"status": "ews_router is alive"}