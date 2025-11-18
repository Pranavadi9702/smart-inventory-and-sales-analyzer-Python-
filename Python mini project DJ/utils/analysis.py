# utils/analysis.py
import pandas as pd
import numpy as np
from scipy.stats import zscore

def moving_average_forecast(series, window=7, periods=30):
    if series is None or len(series) == 0:
        return pd.Series([0]*periods)
    ma = series.rolling(window=window, min_periods=1).mean()
    last = ma.iloc[-1]
    return pd.Series([last]*periods)

def exponential_smoothing(series, alpha=0.3, periods=30):
    if series is None or len(series) == 0:
        return pd.Series([0]*periods)
    s = series.ewm(alpha=alpha, adjust=False).mean()
    last = s.iloc[-1]
    return pd.Series([last]*periods)

def detect_anomalies(series, z_threshold=3.0):
    if series is None or len(series) < 2:
        return pd.Series([False]*len(series), index=series.index if series is not None else [])
    arr = series.fillna(0).values
    z = zscore(arr)
    return pd.Series(np.abs(z) > z_threshold, index=series.index)

def compute_reorder_suggestions(products_df, sales_df, lookback_days=30, safety_factor=1.0):
    today = pd.Timestamp.today().normalize()
    start = today - pd.Timedelta(days=lookback_days)
    if not sales_df.empty:
        sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])
        recent = sales_df[sales_df['sale_date'] >= start]
        demand = recent.groupby('product_id')['quantity'].sum().rename('sold_lookback')
    else:
        demand = pd.Series(dtype=float)
    avg_daily = (demand / lookback_days).reindex(products_df['id']).fillna(0)
    df = products_df.set_index('id').copy()
    df['avg_daily'] = avg_daily
    df['lead_time_days'] = df['lead_time_days'].fillna(7)
    df['lead_time_demand'] = (df['avg_daily'] * df['lead_time_days']).apply(np.ceil)
    df['safety_stock'] = int(np.ceil(df['avg_daily'].std() * safety_factor)) if len(df)>0 else 0
    df['suggested_reorder_qty'] = (df['lead_time_demand'] + df['safety_stock'] - df['stock']).clip(lower=0).astype(int)
    df['need_reorder'] = df['stock'] <= df['reorder_point']
    return df.reset_index()
