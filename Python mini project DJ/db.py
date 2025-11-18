# db.py
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "inventory_app.sqlite3"

def get_conn(timeout=30, check_same_thread=False):
    conn = sqlite3.connect(str(DB_PATH), timeout=timeout, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    return conn

def fetch_products_df(conn):
    return pd.read_sql_query("SELECT * FROM products", conn)

def fetch_sales_df(conn, days=365):
    q = """
    SELECT s.id as id, s.product_id as product_id, s.sale_date as sale_date,
           s.quantity as quantity, p.sku as sku, p.name as name
    FROM sales s
    LEFT JOIN products p ON s.product_id = p.id
    ORDER BY s.sale_date ASC
    """
    df = pd.read_sql_query(q, conn, parse_dates=['sale_date'])
    if df.empty: return df
    cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=days)
    df['sale_date'] = pd.to_datetime(df['sale_date'])
    return df[df['sale_date'] >= cutoff]

def execute(conn, sql, params=None):
    cur = conn.cursor()
    if params:
        cur.execute(sql, params)
    else:
        cur.execute(sql)
    conn.commit()
    return cur

def init_schema(seed_demo=True):
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin'
    );
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        cost REAL DEFAULT 0,
        price REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        reorder_point INTEGER DEFAULT 10,
        lead_time_days INTEGER DEFAULT 7,
        supplier_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        sale_date TEXT,
        quantity INTEGER,
        customer TEXT
    );
    """)
    if seed_demo:
        try:
            cur.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)", ("admin","admin","admin"))
        except Exception:
            pass
    conn.commit()
    cur.close()
    conn.close()
    return True

def seed_sample_products_and_sales():
    import random
    conn = get_conn()
    cur = conn.cursor()
    products = [
        ("SKU-1001", "Blue Widget", 50, 9.99, 10, 7),
        ("SKU-1002", "Red Widget", 30, 14.99, 8, 7),
        ("SKU-1003", "Green Widget", 80, 7.50, 15, 5),
        ("SKU-1004", "Gizmo Pro", 12, 49.99, 5, 10),
    ]
    for sku, name, stock, price, rp, lt in products:
        cur.execute("""
        INSERT OR IGNORE INTO products (sku, name, stock, price, reorder_point, lead_time_days)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (sku, name, stock, price, rp, lt))
    cur.execute("SELECT id FROM products")
    rows = cur.fetchall()
    prod_ids = [r[0] for r in rows] if rows else []
    today = datetime.today().date()
    for _ in range(160):
        if not prod_ids: break
        pid = random.choice(prod_ids)
        days_ago = random.randint(0, 120)
        sale_date = today - timedelta(days=days_ago)
        qty = random.randint(1, 5)
        cust = random.choice(["Walk-in","Online","Retailer A","Retailer B"])
        cur.execute("INSERT INTO sales (product_id, sale_date, quantity, customer) VALUES (?, ?, ?, ?)",
                    (pid, sale_date.isoformat(), qty, cust))
    conn.commit()
    cur.close()
    conn.close()
    return True
