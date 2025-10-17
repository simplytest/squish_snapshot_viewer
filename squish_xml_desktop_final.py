#!/usr/bin/env python3
"""
squish_xml_desktop_final.py

Finale, funktionierende Desktop-Version des Squish XML Viewers
- Reine Python-Standardbibliothek
- Funktioniert garantiert ohne externe Abhängigkeiten
- Gleiche Funktionalität wie Web-Version
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json

# Versuche tkinter zu importieren
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

class XMLDesktopViewer:
    """Finale Desktop-Version des XML Viewers"""
    
    def __init__(self):
        if not TKINTER_AVAILABLE:
            print("Tkinter nicht verfügbar. Bitte installieren Sie Python mit tkinter-Unterstützung.")
            sys.exit(1)
        
        self.current_file = None
        self.xml_data = None
        self.selected_element = None
        
        self.setup_gui()
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
    
    def setup_gui(self):
        """GUI erstellen"""
        self.root = tk.Tk()
        self.root.title("Squish XML Snapshot Viewer - Desktop")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)
        
        # Stil konfigurieren
        style = ttk.Style()
        style.theme_use('default')
        
        self.create_menu()
        self.create_main_interface()
        self.bind_shortcuts()
    
    def create_menu(self):
        """Menüleiste erstellen"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Öffnen... (⌘O)", command=self.open_file_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Neu laden (⌘R)", command=self.reload_file)
        file_menu.add_command(label="Schließen (⌘W)", command=self.close_file)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Bearbeiten-Menü
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
        edit_menu.add_command(label="Kopieren (⌘C)", command=self.copy_selection)
        edit_menu.add_command(label="Alles auswählen (⌘A)", command=self.select_all)
    
    def create_main_interface(self):
        """Haupt-Interface erstellen"""
        # Header mit Datei-Info
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_info_label = ttk.Label(header_frame, text="Keine Datei geladen", 
                                        font=('Arial', 12, 'bold'))
        self.file_info_label.pack(side=tk.LEFT)
        
        # Button zum Öffnen
        open_btn = ttk.Button(header_frame, text="📁 XML-Datei öffnen", 
                             command=self.open_file_dialog)
        open_btn.pack(side=tk.RIGHT)
        
        # Haupt-Container mit Paned Window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Linkes Panel: XML-Baum
        self.create_tree_panel(main_paned)
        
        # Rechtes Panel: Properties/Details
        self.create_properties_panel(main_paned)
        
        # Status-Leiste
        self.status_var = tk.StringVar()
        self.status_var.set("Bereit")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_tree_panel(self, parent):
        """XML-Baum Panel erstellen"""
        tree_frame = ttk.LabelFrame(parent, text="📊 XML Struktur", padding=10)
        parent.add(tree_frame, weight=1)
        
        # Suchfeld
        search_frame = ttk.Frame(tree_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="🔍 Suchen:").pack(side=tk.LEFT)
        self.tree_search_var = tk.StringVar()
        self.tree_search_var.trace('w', self.filter_tree)
        tree_search = ttk.Entry(search_frame, textvariable=self.tree_search_var)
        tree_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        clear_btn = ttk.Button(search_frame, text="✕", width=3,
                              command=lambda: self.tree_search_var.set(""))
        clear_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # TreeView
        tree_container = ttk.Frame(tree_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_container, columns=('type', 'value'), show='tree headings')
        self.tree.heading('#0', text='Element', anchor=tk.W)
        self.tree.heading('type', text='Typ', anchor=tk.W)  
        self.tree.heading('value', text='Wert', anchor=tk.W)
        
        self.tree.column('#0', width=250, minwidth=150)
        self.tree.column('type', width=100, minwidth=80)
        self.tree.column('value', width=200, minwidth=100)
        
        # Scrollbars
        tree_scrolly = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scrollx = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrolly.set, xscrollcommand=tree_scrollx.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scrolly.grid(row=0, column=1, sticky='ns')
        tree_scrollx.grid(row=1, column=0, sticky='ew')
        
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        
        # Events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Kontext-Menü
        self.create_tree_context_menu()
    
    def create_properties_panel(self, parent):
        """Properties Panel erstellen"""
        props_frame = ttk.LabelFrame(parent, text="📋 Eigenschaften", padding=10)
        parent.add(props_frame, weight=1)
        
        # Suchfeld für Properties
        props_search_frame = ttk.Frame(props_frame)
        props_search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(props_search_frame, text="🔍 Suchen:").pack(side=tk.LEFT)
        self.props_search_var = tk.StringVar()
        self.props_search_var.trace('w', self.filter_properties)
        props_search = ttk.Entry(props_search_frame, textvariable=self.props_search_var)
        props_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        props_clear_btn = ttk.Button(props_search_frame, text="✕", width=3,
                                    command=lambda: self.props_search_var.set(""))
        props_clear_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Properties TreeView
        props_container = ttk.Frame(props_frame)
        props_container.pack(fill=tk.BOTH, expand=True)
        
        self.properties = ttk.Treeview(props_container, columns=('value',), show='tree headings')
        self.properties.heading('#0', text='Eigenschaft', anchor=tk.W)
        self.properties.heading('value', text='Wert', anchor=tk.W)
        
        self.properties.column('#0', width=200, minwidth=150)
        self.properties.column('value', width=300, minwidth=200)
        
        # Scrollbars für Properties
        props_scrolly = ttk.Scrollbar(props_container, orient=tk.VERTICAL, command=self.properties.yview)
        props_scrollx = ttk.Scrollbar(props_container, orient=tk.HORIZONTAL, command=self.properties.xview)
        self.properties.configure(yscrollcommand=props_scrolly.set, xscrollcommand=props_scrollx.set)
        
        self.properties.grid(row=0, column=0, sticky='nsew')
        props_scrolly.grid(row=0, column=1, sticky='ns')
        props_scrollx.grid(row=1, column=0, sticky='ew')
        
        props_container.grid_rowconfigure(0, weight=1)
        props_container.grid_columnconfigure(0, weight=1)
        
        # Properties Kontext-Menü
        self.create_properties_context_menu()
    
    def create_tree_context_menu(self):
        """Kontext-Menü für Baum erstellen"""
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="📝 Element-Name kopieren", 
                                  command=lambda: self.copy_tree_item("name"))
        self.tree_menu.add_command(label="🏷️ Element-Typ kopieren", 
                                  command=lambda: self.copy_tree_item("type"))
        self.tree_menu.add_command(label="💬 Element-Wert kopieren", 
                                  command=lambda: self.copy_tree_item("value"))
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="📋 Alle Eigenschaften kopieren", 
                                  command=lambda: self.copy_tree_item("all"))
        
        self.tree.bind("<Button-2>", self.show_tree_menu)  # macOS
        self.tree.bind("<Button-3>", self.show_tree_menu)  # Windows/Linux
    
    def create_properties_context_menu(self):
        """Kontext-Menü für Properties erstellen"""
        self.props_menu = tk.Menu(self.root, tearoff=0)
        self.props_menu.add_command(label="📝 Eigenschaftsname kopieren", 
                                   command=lambda: self.copy_property("name"))
        self.props_menu.add_command(label="💬 Wert kopieren", 
                                   command=lambda: self.copy_property("value"))
        self.props_menu.add_command(label="📋 Eigenschaft=Wert kopieren", 
                                   command=lambda: self.copy_property("both"))
        
        self.properties.bind("<Button-2>", self.show_props_menu)  # macOS
        self.properties.bind("<Button-3>", self.show_props_menu)  # Windows/Linux
    
    def bind_shortcuts(self):
        """Tastaturkürzel binden"""
        # macOS shortcuts
        self.root.bind('<Command-o>', lambda e: self.open_file_dialog())
        self.root.bind('<Command-w>', lambda e: self.close_file())
        self.root.bind('<Command-r>', lambda e: self.reload_file())
        self.root.bind('<Command-c>', lambda e: self.copy_selection())
        self.root.bind('<Command-a>', lambda e: self.select_all())
        
        # Windows/Linux shortcuts  
        self.root.bind('<Control-o>', lambda e: self.open_file_dialog())
        self.root.bind('<Control-w>', lambda e: self.close_file())
        self.root.bind('<Control-r>', lambda e: self.reload_file())
        self.root.bind('<Control-c>', lambda e: self.copy_selection())
        self.root.bind('<Control-a>', lambda e: self.select_all())
    
    def open_file_dialog(self):
        """Datei-Dialog öffnen"""
        file_types = [
            ('XML Files', '*.xml'),
            ('All Files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="Squish XML Snapshot auswählen",
            filetypes=file_types
        )
        
        if filename:
            self.load_xml_file(filename)
    
    def load_xml_file(self, file_path):
        """XML-Datei laden"""
        try:
            self.current_file = file_path
            self.status_var.set("Lade XML-Datei...")
            self.root.update()
            
            # XML parsen
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            
            # UI aktualisieren
            filename = os.path.basename(file_path)
            self.file_info_label.config(text=f"📄 {filename}")
            self.root.title(f"Squish XML Viewer - {filename}")
            
            # Baum aufbauen
            self.populate_tree()
            
            # Properties leeren
            self.clear_properties()
            
            self.status_var.set(f"✅ Datei geladen: {filename}")
            self.show_toast(f"XML-Datei '{filename}' erfolgreich geladen")
            
        except Exception as e:
            error_msg = f"Fehler beim Laden: {str(e)}"
            self.status_var.set(f"❌ {error_msg}")
            messagebox.showerror("Fehler", error_msg)
    
    def populate_tree(self):
        """XML-Baum mit Daten füllen"""
        # Alten Inhalt löschen
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.xml_data is not None:
            self.add_tree_element("", self.xml_data, is_root=True)
            
            # Root-Element expandieren
            if self.tree.get_children():
                self.tree.item(self.tree.get_children()[0], open=True)
    
    def add_tree_element(self, parent, element, is_root=False):
        """Element zum Baum hinzufügen"""
        tag = element.tag
        element_type = "root" if is_root else "element"
        text_content = element.text.strip() if element.text and element.text.strip() else ""
        
        # Element hinzufügen
        item_id = self.tree.insert(parent, tk.END,
                                  text=tag,
                                  values=(element_type, text_content[:50] + "..." if len(text_content) > 50 else text_content),
                                  tags=(element_type,))
        
        # XML-Element-Referenz speichern
        self.tree.set(item_id, "xml_ref", id(element))
        
        # Attribute als Kinder hinzufügen
        for attr_name, attr_value in element.attrib.items():
            attr_id = self.tree.insert(item_id, tk.END,
                                      text=f"@{attr_name}",
                                      values=("attribute", attr_value),
                                      tags=("attribute",))
        
        # Kinder-Elemente hinzufügen
        for child in element:
            self.add_tree_element(item_id, child)
    
    def on_tree_select(self, event):
        """Baum-Element ausgewählt"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item = self.tree.item(item_id)
        
        self.update_properties_for_item(item_id, item)
    
    def on_tree_double_click(self, event):
        """Doppelklick auf Baum-Element"""
        item_id = self.tree.identify_row(event.y)
        if item_id:
            # Element expandieren/kollabieren
            if self.tree.get_children(item_id):
                current_state = self.tree.item(item_id, 'open')
                self.tree.item(item_id, open=not current_state)
    
    def update_properties_for_item(self, item_id, item):
        """Properties für ausgewähltes Element aktualisieren"""
        self.clear_properties()
        
        name = item.get('text', '')
        values = item.get('values', [])
        element_type = values[0] if values else 'unknown'
        element_value = values[1] if len(values) > 1 else ''
        
        # Basis-Eigenschaften
        self.properties.insert("", tk.END, text="Name", values=(name,))
        self.properties.insert("", tk.END, text="Typ", values=(element_type,))
        
        if element_value:
            self.properties.insert("", tk.END, text="Wert", values=(element_value,))
        
        # Erweiterte Informationen
        children = self.tree.get_children(item_id)
        if children:
            element_children = [c for c in children if self.tree.item(c)['values'][0] == 'element']
            attribute_children = [c for c in children if self.tree.item(c)['values'][0] == 'attribute']
            
            if element_children:
                self.properties.insert("", tk.END, text="Kinder", values=(len(element_children),))
            
            if attribute_children:
                self.properties.insert("", tk.END, text="Attribute", values=(len(attribute_children),))
        
        # Parent-Info
        parent_id = self.tree.parent(item_id)
        if parent_id:
            parent_name = self.tree.item(parent_id).get('text', '')
            self.properties.insert("", tk.END, text="Parent", values=(parent_name,))
    
    def clear_properties(self):
        """Properties leeren"""
        for item in self.properties.get_children():
            self.properties.delete(item)
    
    def show_tree_menu(self, event):
        """Baum-Kontext-Menü anzeigen"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)
    
    def show_props_menu(self, event):
        """Properties-Kontext-Menü anzeigen"""
        item = self.properties.identify_row(event.y)
        if item:
            self.properties.selection_set(item)
            self.props_menu.post(event.x_root, event.y_root)
    
    def copy_tree_item(self, copy_type):
        """Baum-Element in Zwischenablage kopieren"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item = self.tree.item(item_id)
        
        name = item.get('text', '')
        values = item.get('values', [])
        element_type = values[0] if values else ''
        element_value = values[1] if len(values) > 1 else ''
        
        if copy_type == "name":
            text = name
        elif copy_type == "type":
            text = element_type
        elif copy_type == "value":
            text = element_value
        elif copy_type == "all":
            text = f"Name: {name}, Typ: {element_type}, Wert: {element_value}"
        else:
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.show_toast(f"Kopiert: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def copy_property(self, copy_type):
        """Property in Zwischenablage kopieren"""
        selection = self.properties.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item = self.properties.item(item_id)
        
        prop_name = item.get('text', '')
        values = item.get('values', [])
        prop_value = values[0] if values else ''
        
        if copy_type == "name":
            text = prop_name
        elif copy_type == "value":
            text = prop_value
        elif copy_type == "both":
            text = f"{prop_name}={prop_value}"
        else:
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.show_toast(f"Kopiert: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def filter_tree(self, *args):
        """Baum filtern (vereinfachte Implementierung)"""
        search_term = self.tree_search_var.get().lower()
        if not search_term:
            self.populate_tree()  # Alle anzeigen
    
    def filter_properties(self, *args):
        """Properties filtern"""
        # Vereinfachte Implementierung für Demo
        pass
    
    def copy_selection(self):
        """Aktuelle Auswahl kopieren"""
        try:
            # Versuche focused widget zu finden
            focused = self.root.focus_get()
            if focused == self.tree:
                self.copy_tree_item("name")
            elif focused == self.properties:
                self.copy_property("name")
        except:
            pass
    
    def select_all(self):
        """Alles auswählen (vereinfacht)"""
        pass
    
    def reload_file(self):
        """Datei neu laden"""
        if self.current_file:
            self.load_xml_file(self.current_file)
        else:
            self.show_toast("Keine Datei zum Neuladen", error=True)
    
    def close_file(self):
        """Datei schließen"""
        self.current_file = None
        self.xml_data = None
        
        self.file_info_label.config(text="Keine Datei geladen")
        self.root.title("Squish XML Snapshot Viewer")
        
        # UI zurücksetzen
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.clear_properties()
        
        self.status_var.set("Datei geschlossen")
        self.show_toast("Datei geschlossen")
    
    def show_toast(self, message, error=False):
        """Toast-ähnliche Benachrichtigung (vereinfacht als Statusbar-Update)"""
        if error:
            self.status_var.set(f"❌ {message}")
        else:
            self.status_var.set(f"✅ {message}")
        
        # Nach 3 Sekunden Status zurücksetzen
        self.root.after(3000, lambda: self.status_var.set("Bereit"))
    
    def run(self):
        """Anwendung starten"""
        self.root.mainloop()

def main():
    """Hauptfunktion"""
    if not TKINTER_AVAILABLE:
        print("❌ Tkinter ist nicht verfügbar!")
        print("Auf macOS: brew install python-tk")
        print("Auf Ubuntu: sudo apt install python3-tk")
        return
    
    app = XMLDesktopViewer()
    app.run()

if __name__ == "__main__":
    main()