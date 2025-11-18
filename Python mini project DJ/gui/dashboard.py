# gui/dashboard.py
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from db import get_conn, fetch_sales_df, fetch_products_df
from utils.analysis import moving_average_forecast, detect_anomalies, compute_reorder_suggestions
import pandas as pd
import numpy as np

class Dashboard(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill='both', expand=True)
        self.create_ui()
        self.refresh()

    def create_ui(self):
        top = ctk.CTkFrame(self); top.pack(fill='x', padx=12, pady=8)
        ctk.CTkButton(top, text="Refresh", command=self.refresh).pack(side='left')
        # KPI cards
        cardp = ctk.CTkFrame(self); cardp.pack(fill='x', padx=12, pady=6)
        self.kpi_total_sales = ctk.CTkLabel(cardp, text="Total Sales: --", font=ctk.CTkFont(size=16, weight="bold"))
        self.kpi_total_sales.pack(side='left', padx=12)
        self.kpi_top_sku = ctk.CTkLabel(cardp, text="Top SKU: --", font=ctk.CTkFont(size=14))
        self.kpi_top_sku.pack(side='left', padx=12)

        # Charts area
        chart_frame = ctk.CTkFrame(self); chart_frame.pack(fill='both', expand=True, padx=12, pady=6)
        self.fig = Figure(figsize=(10,5), tight_layout=True)
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Reorder suggestions table
        self.reorder_frame = ctk.CTkFrame(self); self.reorder_frame.pack(fill='x', padx=12, pady=6)
        import tkinter as tk
        cols = ('sku','name','stock','reorder_point','suggest_qty','risk')
        self.tree = tk.ttk.Treeview(self.reorder_frame, columns=cols, show='headings', height=6)
        for c in cols:
            self.tree.heading(c, text=c.title()); self.tree.column(c, width=140)
        self.tree.pack(fill='both', expand=True)

    def refresh(self):
        conn = get_conn()
        sales = fetch_sales_df(conn, days=365)
        prods = fetch_products_df(conn)
        conn.close()

        if not sales.empty:
            sales['sale_date'] = pd.to_datetime(sales['sale_date'])
            daily = sales.groupby('sale_date')['quantity'].sum().asfreq('D', fill_value=0)
        else:
            daily = pd.Series(dtype=float)

        self.ax1.clear(); self.ax2.clear()
        if len(daily)>0:
            self.ax1.plot(daily.index, daily.values, marker='o', linewidth=1, label='Actual')
            forecast = moving_average_forecast(daily, window=7, periods=30)
            fut_idx = pd.date_range(start=daily.index[-1]+pd.Timedelta(days=1), periods=len(forecast))
            self.ax1.plot(fut_idx, forecast.values, linestyle='--', label='Forecast (MA)')
            self.ax1.set_title("Daily Sales & Forecast")
            self.ax1.legend()
            anom = detect_anomalies(daily, z_threshold=3.0)
            self.ax2.bar(daily.index, daily.values)
            if anom.any():
                self.ax2.scatter(daily[anom].index, daily[anom].values, color='red', s=40)
            self.ax2.set_title("Daily Sales with Anomalies")
        else:
            self.ax1.text(0.5,0.5,"No sales data", ha='center')
            self.ax2.text(0.5,0.5,"No sales data", ha='center')
        self.fig.autofmt_xdate()
        self.canvas.draw()

        # KPIs
        total_sales = sales['quantity'].sum() if not sales.empty else 0
        self.kpi_total_sales.configure(text=f"Total Units Sold: {int(total_sales)}")
        if not sales.empty:
            top = sales.groupby('sku')['quantity'].sum().sort_values(ascending=False)
            top_sku = top.index[0] if len(top)>0 else "--"
            self.kpi_top_sku.configure(text=f"Top SKU: {top_sku}")
        else:
            self.kpi_top_sku.configure(text="Top SKU: --")

        # Reorder suggestions
        reorder_df = compute_reorder_suggestions(prods, sales, lookback_days=30, safety_factor=1.0)
        for r in self.tree.get_children(): self.tree.delete(r)
        for _,row in reorder_df.sort_values('suggested_reorder_qty', ascending=False).iterrows():
            risk = "High" if row['need_reorder'] else ("Medium" if row['suggested_reorder_qty']>0 else "Safe")
            self.tree.insert('', 'end', values=(row['sku'], row['name'], int(row['stock']), int(row['reorder_point']), int(row['suggested_reorder_qty']), risk))
