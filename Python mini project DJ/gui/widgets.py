# gui/widgets.py
import customtkinter as ctk
from tkinter import PhotoImage

ctk.set_appearance_mode("dark")   # "dark" / "light"
ctk.set_default_color_theme("dark-blue")

class SidebarButton(ctk.CTkButton):
    def __init__(self, master, text, command=None, **kwargs):
        super().__init__(master, text=text, command=command, corner_radius=8, height=40, **kwargs)

def icon_label(master, text):
    return ctk.CTkLabel(master, text=text, font=ctk.CTkFont(size=14, weight="bold"))
