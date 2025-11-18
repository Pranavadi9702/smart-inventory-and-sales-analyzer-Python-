# gui/sales.py
import customtkinter as ctk
from tkinter import messagebox
from db import get_conn, fetch_products_df, execute
import pandas as pd

class SalesPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.pack(fill='both', expand=True)
        self.cart = []  # list of (product_id, sku, name, qty)
        self.create_ui()
        self.load_products_list()

    def create_ui(self):
        top = ctk.CTkFrame(self)
        top.pack(fill='x', padx=12, pady=8)
        self.prod_var = ctk.StringVar()
        self.qty_var = ctk.StringVar(value='1')
        ctk.CTkEntry(top, placeholder_text="Search SKU or name...", width=300, textvariable=self.prod_var).pack(side='left', padx=6)
        ctk.CTkEntry(top, placeholder_text="Qty", width=80, textvariable=self.qty_var).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Add to Cart", command=self.add_to_cart).pack(side='left', padx=6)
        ctk.CTkButton(top, text="Checkout", fg_color="#10b981", command=self.checkout).pack(side='left', padx=6)

        mid = ctk.CTkFrame(self)
        mid.pack(fill='both', expand=True, padx=12, pady=8)
        # left: available products list
        self.left_frame = ctk.CTkFrame(mid); self.left_frame.pack(side='left', fill='both', expand=True, padx=6)
        self.right_frame = ctk.CTkFrame(mid); self.right_frame.pack(side='left', fill='y', padx=6)

        # product list as Treeview
        import tkinter as tk
        cols = ('id','sku','name','stock','price')
        self.prod_tree = tk.ttk.Treeview(self.left_frame, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.prod_tree.heading(c, text=c.title()); self.prod_tree.column(c, width=120)
        self.prod_tree.pack(fill='both', expand=True)
        self.prod_tree.bind('<Double-1>', self.quick_add)

        # cart area (listbox)
        ctk.CTkLabel(self.right_frame, text="Cart").pack(anchor='nw', pady=4)
        self.cart_box = ctk.CTkTextbox(self.right_frame, width=320, height=360)
        self.cart_box.pack(padx=6, pady=6)
        ctk.CTkButton(self.right_frame, text="Clear Cart", command=self.clear_cart).pack(pady=6)

    def load_products_list(self):
        conn = get_conn()
        df = fetch_products_df(conn)
        conn.close()
        import tkinter as tk
        for r in self.prod_tree.get_children(): self.prod_tree.delete(r)
        for _,row in df.iterrows():
            self.prod_tree.insert('', 'end', values=(int(row['id']), row['sku'], row['name'], int(row['stock']), float(row['price'])))

    def add_to_cart(self):
        sku = self.prod_var.get().strip()
        try:
            qty = int(self.qty_var.get())
        except Exception:
            messagebox.showerror("Error","Invalid qty"); return
        if not sku:
            messagebox.showerror("Error","Enter product SKU or double click item"); return
        conn = get_conn(); df = fetch_products_df(conn); conn.close()
        matched = df[df['sku']==sku]
        if matched.empty:
            messagebox.showerror("Error","SKU not found"); return
        row = matched.iloc[0]
        if int(row['stock']) < qty:
            messagebox.showerror("Error","Insufficient stock"); return
        self.cart.append((int(row['id']), row['sku'], row['name'], qty, float(row['price'])))
        self.refresh_cart_display()

    def quick_add(self, event):
        sel = self.prod_tree.selection()
        if not sel: return
        vals = self.prod_tree.item(sel[0])['values']
        pid, sku, name, stock, price = vals
        if int(stock) <= 0:
            messagebox.showerror("Error","Out of stock"); return
        self.cart.append((int(pid), sku, name, 1, float(price)))
        self.refresh_cart_display()

    def refresh_cart_display(self):
        self.cart_box.delete("0.0","end")
        total = 0.0
        for pid, sku, name, qty, price in self.cart:
            line = f"{sku} | {name} x{qty} @ {price} = {qty*price}\n"
            total += qty*price
            self.cart_box.insert("end", line)
        self.cart_box.insert("end", f"\nTotal: {total:.2f}")

    def clear_cart(self):
        self.cart = []
        self.refresh_cart_display()

    def checkout(self):
        if not self.cart:
            messagebox.showerror("Error","Cart empty"); return
        conn = get_conn()
        cur = conn.cursor()
        try:
            for pid, sku, name, qty, price in self.cart:
                cur.execute("INSERT INTO sales (product_id, sale_date, quantity, customer) VALUES (?, ?, ?, ?)",
                            (pid, datetime.today().date().isoformat(), qty, "Walk-in"))
                cur.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, pid))
            conn.commit()
            messagebox.showinfo("Sale","Checkout completed")
            self.clear_cart(); self.load_products_list()
        except Exception as e:
            conn.rollback(); messagebox.showerror("DB Error", str(e))
        finally:
            cur.close(); conn.close()
