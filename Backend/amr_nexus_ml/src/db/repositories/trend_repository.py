from sqlalchemy import func
from datetime import datetime, timedelta
import pandas as pd
from src.db.database import SessionLocal
from src.db.models import YourDataModel

def get_monthly_mdr_rates(county: str = None, months: int = 12):
    session = SessionLocal()
    try:
        query = session.query(
            func.date_trunc('month', YourDataModel.collection_date).label('month_date'),
            func.avg(func.cast(YourDataModel.is_mdr, func.Float)).label('mdr_rate')
        )
        cutoff_date = datetime.now() - timedelta(days=months * 31)
        query = query.filter(YourDataModel.collection_date >= cutoff_date)
        if county:
            query = query.filter(YourDataModel.county == county)
        query = query.group_by('month_date').order_by('month_date')
        result = query.all()
        df = pd.DataFrame(result, columns=['month_date', 'mdr_rate'])
        return df
    finally:
        session.close()