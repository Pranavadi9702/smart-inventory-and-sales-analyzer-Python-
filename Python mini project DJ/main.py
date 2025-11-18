# main.py
import customtkinter as ctk
from gui.widgets import SidebarButton
from gui.dashboard import Dashboard
from gui.products import ProductsPanel
from gui.sales import SalesPanel
from gui.reports import ReportsPanel
from db import init_schema, seed_sample_products_and_sales
import os, sys

APP_TITLE = "InventoGen — Inventory Intelligence"
APP_SIZE = "1200x760"

def create_app():
    init_schema(seed_demo=True)
    # seed sample data only if DB is empty (optional)
    if not os.path.exists("inventory_app.sqlite3"):
        # already created by init_schema; then seed sample
        seed_sample_products_and_sales()

    app = ctk.CTk()
    app.title(APP_TITLE)
    app.geometry(APP_SIZE)
    # layout
    sidebar = ctk.CTkFrame(app, width=200)
    sidebar.pack(side='left', fill='y', padx=8, pady=8)
    content = ctk.CTkFrame(app)
    content.pack(side='left', fill='both', expand=True, padx=8, pady=8)

    # navigation buttons
    btn_dash = SidebarButton(sidebar, text="Dashboard")
    btn_prod = SidebarButton(sidebar, text="Products")
    btn_sales = SidebarButton(sidebar, text="Sales")
    btn_reports = SidebarButton(sidebar, text="Reports")
    btn_dash.pack(pady=6, padx=12); btn_prod.pack(pady=6, padx=12); btn_sales.pack(pady=6, padx=12); btn_reports.pack(pady=6, padx=12)

    frames = {}
    frames['dashboard'] = Dashboard(content)
    frames['products'] = ProductsPanel(content)
    frames['sales'] = SalesPanel(content)
    frames['reports'] = ReportsPanel(content)
    for f in frames.values():
        f.place(in_=content, x=0, y=0, relwidth=1, relheight=1)

    def show(key):
        for k,f in frames.items():
            if k==key: f.lift()
            else: f.lower()

    btn_dash.configure(command=lambda: show('dashboard'))
    btn_prod.configure(command=lambda: show('products'))
    btn_sales.configure(command=lambda: show('sales'))
    btn_reports.configure(command=lambda: show('reports'))

    show('dashboard')
    return app

if __name__ == "__main__":
    app = create_app()
    app.mainloop()
