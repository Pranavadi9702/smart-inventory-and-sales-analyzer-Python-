# gui/products.py
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from db import get_conn, fetch_products_df, execute
import pandas as pd
import uuid

class ProductsPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill='both', expand=True)
        self.create_ui()
        self.load_products()

    def create_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill='x', padx=12, pady=8)
        self.search_var = ctk.StringVar()
        ctk.CTkEntry(top, placeholder_text="Search SKU or name...", textvariable=self.search_var, width=300).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Search", command=self.load_products).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Add Product", fg_color="#3b82f6", command=self.add_dialog).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Import CSV", command=self.import_csv).pack(side='left', padx=6)

        # Treeview-like table using tkinter Treeview (styled)
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill='both', expand=True, padx=12, pady=8)
        cols = ('id','sku','name','stock','price','reorder_point','lead_time_days')
        self.tree = tk.ttk.Treeview(self.table_frame, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=120)
        self.tree.pack(fill='both', expand=True, side='left')
        scroll = tk.Scrollbar(self.table_frame, command=self.tree.yview)
        scroll.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind('<Double-1>', self.on_double)

    def load_products(self):
        conn = get_conn()
        df = fetch_products_df(conn)
        conn.close()
        q = self.search_var.get().strip().lower()
        if q:
            df = df[df['sku'].str.lower().str.contains(q) | df['name'].str.lower().str.contains(q)]
        for r in self.tree.get_children(): self.tree.delete(r)
        for _, row in df.iterrows():
            self.tree.insert('', 'end', values=(int(row['id']), row['sku'], row['name'], int(row['stock']), float(row['price']), int(row.get('reorder_point') or 0), int(row.get('lead_time_days') or 7)))

    def add_dialog(self):
        d = ctk.CTkToplevel(self)
        d.title("Add Product")
        entries = {}
        for label in ["SKU","Name","Stock","Price","Reorder Point","Lead Time Days"]:
            ctk.CTkLabel(d, text=label).pack(anchor='w', padx=12, pady=2)
            e = ctk.CTkEntry(d, width=300)
            e.pack(padx=12, pady=2)
            entries[label] = e
        # pre-generate SKU
        entries['SKU'].insert(0, f"SKU-{uuid.uuid4().hex[:6].upper()}")
        entries['Stock'].insert(0,'0'); entries['Reorder Point'].insert(0,'10'); entries['Lead Time Days'].insert(0,'7')
        def do_add():
            sku = entries['SKU'].get().strip(); name = entries['Name'].get().strip()
            if not sku or not name:
                messagebox.showerror("Error","SKU and Name required"); return
            try:
                stock = int(entries['Stock'].get() or 0)
                price = float(entries['Price'].get() or 0)
                rp = int(entries['Reorder Point'].get() or 10)
                lt = int(entries['Lead Time Days'].get() or 7)
            except Exception:
                messagebox.showerror("Error","Invalid numeric value"); return
            conn = get_conn()
            try:
                execute(conn, "INSERT INTO products (sku,name,stock,price,reorder_point,lead_time_days) VALUES (?,?,?,?,?,?)", (sku,name,stock,price,rp,lt))
                messagebox.showinfo("Added","Product added"); d.destroy(); self.load_products()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                conn.close()
        ctk.CTkButton(d, text="Add", command=do_add).pack(pady=12)

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        df = pd.read_csv(path)
        # expected columns: sku,name,stock,price,reorder_point,lead_time_days
        conn = get_conn()
        cur = conn.cursor()
        count = 0
        for _, row in df.iterrows():
            try:
                cur.execute("INSERT OR IGNORE INTO products (sku,name,stock,price,reorder_point,lead_time_days) VALUES (?,?,?,?,?,?)",
                            (str(row.get('sku')), str(row.get('name')), int(row.get('stock') or 0), float(row.get('price') or 0), int(row.get('reorder_point') or 10), int(row.get('lead_time_days') or 7)))
                count += 1
            except Exception:
                pass
        conn.commit(); conn.close()
        messagebox.showinfo("Import", f"Imported approx {count} rows"); self.load_products()

    def on_double(self, event):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0])['values']
        pid, sku, name, stock, price, rp, lt = vals
        d = ctk.CTkToplevel(self)
        d.title("Edit Product")
        sku_e = ctk.CTkEntry(d); sku_e.pack(padx=12, pady=6); sku_e.insert(0,sku)
        name_e = ctk.CTkEntry(d); name_e.pack(padx=12, pady=6); name_e.insert(0,name)
        stock_e = ctk.CTkEntry(d); stock_e.pack(padx=12, pady=6); stock_e.insert(0,stock)
        price_e = ctk.CTkEntry(d); price_e.pack(padx=12, pady=6); price_e.insert(0,price)
        def do_save():
            try:
                s = sku_e.get().strip(); n = name_e.get().strip()
                st = int(stock_e.get()); pr = float(price_e.get())
            except Exception:
                messagebox.showerror("Error","Invalid values"); return
            conn = get_conn()
            try:
                execute(conn, "UPDATE products SET sku=?,name=?,stock=?,price=? WHERE id=?", (s,n,st,pr,int(pid)))
                messagebox.showinfo("Saved","Product updated"); d.destroy(); self.load_products()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))
            finally:
                conn.close()
        ctk.CTkButton(d, text="Save", command=do_save).pack(pady=8)
