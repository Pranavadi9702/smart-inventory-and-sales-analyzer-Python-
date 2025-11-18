# utils/export.py
import pandas as pd

def export_df_to_csv(df, path):
    df.to_csv(path, index=False)

def export_df_to_excel(df_map, path):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, df in df_map.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
