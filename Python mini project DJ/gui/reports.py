# gui/reports.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from db import get_conn, fetch_products_df, fetch_sales_df
from utils.export import export_df_to_excel
import pandas as pd

class ReportsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill='both', expand=True)
        self.create_ui()

    def create_ui(self):
        top = ctk.CTkFrame(self); top.pack(fill='x', padx=12, pady=8)
        ctk.CTkButton(top, text="Export Excel (Products+Sales+Pivot)", command=self.export_summary).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Export Products CSV", command=self.export_products_csv).pack(side='left', padx=6)
        self.log = ctk.CTkTextbox(self, height=10)
        self.log.pack(fill='both', expand=True, padx=12, pady=8)

    def log_msg(self, s):
        self.log.insert("end", s+"\n"); self.log.see("end")

    def export_products_csv(self):
        conn = get_conn(); df = fetch_products_df(conn); conn.close()
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not path: return
        df.to_csv(path, index=False)
        self.log_msg(f"Products exported: {path}")

    def export_summary(self):
        conn = get_conn()
        prods = fetch_products_df(conn)
        sales = fetch_sales_df(conn, days=3650)
        conn.close()
        if not sales.empty:
            sales['sale_date'] = pd.to_datetime(sales['sale_date'])
            sales['month'] = sales['sale_date'].dt.to_period('M').astype(str)
            pivot = sales.groupby(['month','sku'])['quantity'].sum().reset_index().pivot(index='sku', columns='month', values='quantity').fillna(0)
        else:
            pivot = pd.DataFrame()
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if not path: return
        export_df_to_excel({'products': prods, 'sales': sales, 'monthly_by_product': pivot.reset_index()}, path)
        self.log_msg(f"Summary exported: {path}")
