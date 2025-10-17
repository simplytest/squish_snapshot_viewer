#!/usr/bin/env python3
"""Einfacher tkinter Test"""

import tkinter as tk
from tkinter import ttk, messagebox

def test_tkinter():
    root = tk.Tk()
    root.title("Tkinter Test")
    root.geometry("400x300")
    
    label = ttk.Label(root, text="Tkinter funktioniert!")
    label.pack(pady=20)
    
    button = ttk.Button(root, text="Test Toast", 
                       command=lambda: messagebox.showinfo("Test", "Tkinter ist verfügbar!"))
    button.pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_tkinter()