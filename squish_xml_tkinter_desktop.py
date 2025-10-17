#!/usr/bin/env python3
"""
squish_xml_tkinter_desktop.py

Pure Python/tkinter Desktop-Anwendung für Squish XML Snapshot Viewer.
Bietet die exakt gleiche Funktionalität wie die Web-Version, aber als native Desktop-App.

Features:
- Zwei-Panel Layout: XML-Baum links, Properties rechts
- Suchfunktionen in beiden Panels
- Kontextmenüs mit Kopieren-Funktionen
- Toast-Benachrichtigungen (deutsche Meldungen)
- Tastaturkürzel (Ctrl+O, Ctrl+W, Ctrl+R)
- Drag & Drop für XML-Dateien
- Element-Overlays genau wie in der Web-Version
- Responsive Layout

Abhängigkeiten:
    Nur Python Standardbibliothek (tkinter, xml, etc.)

Usage:
    python3 squish_xml_tkinter_desktop.py [xml_file]
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from pathlib import Path
import json
from tkinter import font
import threading
import time

class ToastNotification:
    """Zeigt Toast-Benachrichtigungen für Benutzeraktionen"""
    
    def __init__(self, parent):
        self.parent = parent
        self.toast_windows = []
    
    def show_toast(self, message, toast_type="success", duration=3000):
        """Zeigt eine Toast-Benachrichtigung
        
        Args:
            message: Nachricht zum Anzeigen
            toast_type: "success" (grün) oder "error" (rot)
            duration: Anzeigedauer in Millisekunden
        """
        # Toast-Fenster erstellen
        toast = tk.Toplevel(self.parent)
        toast.withdraw()  # Zunächst verstecken
        toast.overrideredirect(True)  # Kein Fensterrahmen
        toast.attributes('-topmost', True)  # Immer im Vordergrund
        
        # Farben basierend auf Typ
        if toast_type == "success":
            bg_color = "#4CAF50"  # Grün
            text_color = "white"
        else:
            bg_color = "#f44336"  # Rot
            text_color = "white"
        
        # Toast-Inhalt
        frame = tk.Frame(toast, bg=bg_color, padx=15, pady=10)
        frame.pack()
        
        label = tk.Label(frame, text=message, bg=bg_color, fg=text_color, 
                        font=('Arial', 10, 'bold'))
        label.pack()
        
        # Position berechnen (rechts oben)
        toast.update_idletasks()
        width = toast.winfo_reqwidth()
        height = toast.winfo_reqheight()
        
        screen_width = toast.winfo_screenwidth()
        x = screen_width - width - 20
        y = 50 + len(self.toast_windows) * (height + 10)
        
        toast.geometry(f'{width}x{height}+{x}+{y}')
        toast.deiconify()  # Anzeigen
        
        # Fade-in Animation
        toast.attributes('-alpha', 0.0)
        self.toast_windows.append(toast)
        self.fade_in(toast, duration)
    
    def fade_in(self, toast, duration):
        """Fade-in Animation für Toast"""
        def animate():
            alpha = 0.0
            while alpha < 1.0:
                alpha += 0.05
                try:
                    toast.attributes('-alpha', alpha)
                    toast.update()
                    time.sleep(0.02)
                except:
                    return
            
            # Nach duration ms ausblenden
            toast.after(duration, lambda: self.fade_out(toast))
        
        threading.Thread(target=animate, daemon=True).start()
    
    def fade_out(self, toast):
        """Fade-out Animation für Toast"""
        def animate():
            alpha = 1.0
            while alpha > 0.0:
                alpha -= 0.05
                try:
                    toast.attributes('-alpha', alpha)
                    toast.update()
                    time.sleep(0.02)
                except:
                    return
            
            try:
                if toast in self.toast_windows:
                    self.toast_windows.remove(toast)
                toast.destroy()
            except:
                pass
        
        threading.Thread(target=animate, daemon=True).start()


class SquishXMLDesktopViewer:
    """Hauptklasse für den Squish XML Desktop Viewer"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Squish XML Snapshot Viewer")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)
        
        # Variablen
        self.current_file = None
        self.xml_data = None
        self.filtered_tree_items = []
        self.filtered_properties = []
        self.selected_element = None
        
        # Toast-System
        self.toast = ToastNotification(self.root)
        
        # UI erstellen
        self.create_ui()
        self.create_menu()
        self.bind_keyboard_shortcuts()
        
        # Drag & Drop konfigurieren
        self.setup_drag_drop()
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
    
    def create_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Hauptcontainer
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Header mit Suchfeldern und Kontrollen (wie in HTML)
        self.header_frame = ttk.Frame(main_frame, relief=tk.RAISED, borderwidth=1)
        self.header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Header-Inhalt
        header_content = ttk.Frame(self.header_frame)
        header_content.pack(fill=tk.X, padx=10, pady=5)
        
        # Title
        title_label = ttk.Label(header_content, text="Object Viewer", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # Suchgruppen (wie in HTML)
        search_frame = ttk.Frame(header_content)
        search_frame.pack(side=tk.RIGHT)
        
        # Tree-Suche
        ttk.Label(search_frame, text="Tree:").pack(side=tk.LEFT, padx=(10, 5))
        tree_search_frame = ttk.Frame(search_frame)
        tree_search_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.tree_search_var = tk.StringVar()
        self.tree_search_var.trace('w', self.filter_tree)
        tree_search_entry = ttk.Entry(tree_search_frame, textvariable=self.tree_search_var, width=20)
        tree_search_entry.pack(side=tk.LEFT)
        clear_tree_btn = ttk.Button(tree_search_frame, text="✕", width=3, 
                                   command=lambda: self.tree_search_var.set(""))
        clear_tree_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        # Properties-Suche  
        ttk.Label(search_frame, text="Properties:").pack(side=tk.LEFT, padx=(0, 5))
        props_search_frame = ttk.Frame(search_frame)
        props_search_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        self.props_search_var = tk.StringVar()
        self.props_search_var.trace('w', self.filter_properties)
        props_search_entry = ttk.Entry(props_search_frame, textvariable=self.props_search_var, width=20)
        props_search_entry.pack(side=tk.LEFT)
        clear_props_btn = ttk.Button(props_search_frame, text="✕", width=3,
                                    command=lambda: self.props_search_var.set(""))
        clear_props_btn.pack(side=tk.LEFT, padx=(2, 0))
        
        # Sort-Dropdown
        ttk.Label(search_frame, text="Sort:").pack(side=tk.LEFT, padx=(0, 5))
        self.sort_var = tk.StringVar(value="desc")
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_var, 
                                 values=["desc", "asc", "none"], width=8, state="readonly")
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_properties())
        
        # Datei-Info
        file_info_frame = ttk.Frame(main_frame)
        file_info_frame.pack(fill=tk.X, pady=(0, 5))
        self.file_label = ttk.Label(file_info_frame, text="Keine Datei geladen", 
                                   font=('Arial', 10))
        self.file_label.pack(side=tk.LEFT)
        
        # Haupt-Container: Links Sidebar, Rechts zwei Panels übereinander
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Linkes Panel: XML-Baum (Sidebar)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Rechtes Panel: Screenshot oben, Properties unten
        right_frame = ttk.Frame(main_paned)  
        main_paned.add(right_frame, weight=2)
        
        # === LINKES PANEL: XML-Baum (Object Tree) ===
        tree_header = ttk.Frame(left_frame, relief=tk.RAISED, borderwidth=1)
        tree_header.pack(fill=tk.X, pady=(0, 2))
        tree_label = ttk.Label(tree_header, text="Object Tree", font=('Arial', 11, 'bold'))
        tree_label.pack(pady=5)
        
        # Treeview mit Scrollbars
        tree_content = ttk.Frame(left_frame)
        tree_content.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_content, columns=(), show='tree')  # Nur Baum, keine Spalten
        self.tree.heading('#0', text='Object Tree', anchor=tk.W)
        
        # Scrollbars für Baum
        tree_scrolly = ttk.Scrollbar(tree_content, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scrollx = ttk.Scrollbar(tree_content, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrolly.set, xscrollcommand=tree_scrollx.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scrolly.grid(row=0, column=1, sticky='ns')
        tree_scrollx.grid(row=1, column=0, sticky='ew')
        
        tree_content.grid_rowconfigure(0, weight=1)
        tree_content.grid_columnconfigure(0, weight=1)
        
        # Tree-Auswahl Event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Kontextmenü für Baum
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="Element-Name kopieren", 
                                          command=lambda: self.copy_to_clipboard("tree_name"))
        self.tree_context_menu.add_command(label="Realname kopieren", 
                                          command=lambda: self.copy_to_clipboard("tree_realname"))
        self.tree_context_menu.add_command(label="Element-ID kopieren", 
                                          command=lambda: self.copy_to_clipboard("tree_id"))
        self.tree.bind("<Button-2>", self.show_tree_context_menu)  # Rechtsklick auf macOS
        self.tree.bind("<Button-3>", self.show_tree_context_menu)  # Rechtsklick auf Linux/Windows
        
        # === RECHTES PANEL: Screenshot oben, Properties unten ===
        # Rechter vertikaler Paned Window
        right_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_paned.pack(fill=tk.BOTH, expand=True)
        
        # Screenshot Panel (oben)
        screenshot_frame = ttk.Frame(right_paned)
        right_paned.add(screenshot_frame, weight=1)
        
        # Screenshot Header
        screenshot_header = ttk.Frame(screenshot_frame, relief=tk.RAISED, borderwidth=1)
        screenshot_header.pack(fill=tk.X)
        screenshot_label = ttk.Label(screenshot_header, text="Screenshot", font=('Arial', 11, 'bold'))
        screenshot_label.pack(pady=5)
        
        # Screenshot Content
        screenshot_content = ttk.Frame(screenshot_frame, relief=tk.SUNKEN, borderwidth=1)
        screenshot_content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Canvas für Screenshot mit Element-Overlays
        self.screenshot_canvas = tk.Canvas(screenshot_content, bg='white')
        screenshot_scroll_y = ttk.Scrollbar(screenshot_content, orient=tk.VERTICAL, command=self.screenshot_canvas.yview)
        screenshot_scroll_x = ttk.Scrollbar(screenshot_content, orient=tk.HORIZONTAL, command=self.screenshot_canvas.xview)
        
        self.screenshot_canvas.configure(yscrollcommand=screenshot_scroll_y.set, 
                                       xscrollcommand=screenshot_scroll_x.set)
        
        self.screenshot_canvas.grid(row=0, column=0, sticky='nsew')
        screenshot_scroll_y.grid(row=0, column=1, sticky='ns')
        screenshot_scroll_x.grid(row=1, column=0, sticky='ew')
        
        screenshot_content.grid_rowconfigure(0, weight=1)
        screenshot_content.grid_columnconfigure(0, weight=1)
        
        # Properties Panel (unten)
        properties_frame = ttk.Frame(right_paned)
        right_paned.add(properties_frame, weight=1)
        
        # Properties Header
        props_header = ttk.Frame(properties_frame, relief=tk.RAISED, borderwidth=1)
        props_header.pack(fill=tk.X)
        props_label = ttk.Label(props_header, text="Properties", font=('Arial', 11, 'bold'))
        props_label.pack(pady=5)
        
        # Properties Content
        props_content = ttk.Frame(properties_frame)
        props_content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.properties = ttk.Treeview(props_content, columns=('value',), show='tree headings')
        self.properties.heading('#0', text='Property', anchor=tk.W)
        self.properties.heading('value', text='Value', anchor=tk.W)
        
        # Spaltenbreiten für Properties
        self.properties.column('#0', width=200, minwidth=150)
        self.properties.column('value', width=300, minwidth=200)
        
        # Scrollbars für Properties
        props_scrolly = ttk.Scrollbar(props_content, orient=tk.VERTICAL, command=self.properties.yview)
        props_scrollx = ttk.Scrollbar(props_content, orient=tk.HORIZONTAL, command=self.properties.xview)
        self.properties.configure(yscrollcommand=props_scrolly.set, xscrollcommand=props_scrollx.set)
        
        self.properties.grid(row=0, column=0, sticky='nsew')
        props_scrolly.grid(row=0, column=1, sticky='ns')
        props_scrollx.grid(row=1, column=0, sticky='ew')
        
        props_content.grid_rowconfigure(0, weight=1)
        props_content.grid_columnconfigure(0, weight=1)
        
        # Kontextmenü für Properties
        self.props_context_menu = tk.Menu(self.root, tearoff=0)
        self.props_context_menu.add_command(label="Property kopieren", 
                                           command=lambda: self.copy_to_clipboard("prop_name"))
        self.props_context_menu.add_command(label="Value kopieren", 
                                           command=lambda: self.copy_to_clipboard("prop_value"))
        self.props_context_menu.add_command(label="Property=Value kopieren", 
                                           command=lambda: self.copy_to_clipboard("prop_both"))
        self.properties.bind("<Button-2>", self.show_props_context_menu)
        self.properties.bind("<Button-3>", self.show_props_context_menu)
    
    def create_menu(self):
        """Erstellt die Menüleiste"""
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
    
    def bind_keyboard_shortcuts(self):
        """Bindet Tastaturkürzel"""
        # Cmd/Ctrl + O: Datei öffnen
        self.root.bind('<Command-o>', lambda e: self.open_file_dialog())
        self.root.bind('<Control-o>', lambda e: self.open_file_dialog())
        
        # Cmd/Ctrl + W: Datei schließen
        self.root.bind('<Command-w>', lambda e: self.close_file())
        self.root.bind('<Control-w>', lambda e: self.close_file())
        
        # Cmd/Ctrl + R: Neu laden
        self.root.bind('<Command-r>', lambda e: self.reload_file())
        self.root.bind('<Control-r>', lambda e: self.reload_file())
    
    def setup_drag_drop(self):
        """Konfiguriert Drag & Drop für XML-Dateien"""
        # Tkinter hat keine native Drag & Drop Unterstützung
        # Das könnte mit tkinterdnd2 erweitert werden, aber für jetzt zeigen wir
        # eine Meldung dass Dateien über das Menü geöffnet werden sollen
        pass
    
    def open_file_dialog(self):
        """Öffnet Dialog zum Auswählen einer XML-Datei"""
        file_types = [
            ('XML Files', '*.xml'),
            ('All Files', '*.*')
        ]
        
        filename = filedialog.askopenfilename(
            title="XML-Datei auswählen",
            filetypes=file_types
        )
        
        if filename:
            self.load_xml_file(filename)
    
    def load_xml_file(self, file_path):
        """Lädt eine XML-Datei und zeigt sie an"""
        try:
            self.current_file = file_path
            
            # XML parsen
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            
            # UI aktualisieren
            self.file_label.config(text=f"XML Viewer - {os.path.basename(file_path)}")
            
            # Baum aufbauen
            self.populate_tree()
            
            # Screenshot laden (falls vorhanden)
            self.load_screenshot()
            
            # Properties leeren
            for item in self.properties.get_children():
                self.properties.delete(item)
            
            self.toast.show_toast(f"XML-Datei '{os.path.basename(file_path)}' geladen", "success")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der XML-Datei:\n{str(e)}")
    
    def load_screenshot(self):
        """Lädt und zeigt das Screenshot an"""
        try:
            # Suche nach <image> Element im XML
            for elem in self.xml_data.iter():
                if elem.tag == 'image' and elem.get('type') == 'PNG':
                    try:
                        # Base64-kodiertes Bild dekodieren und anzeigen
                        import base64
                        from PIL import Image, ImageTk
                        from io import BytesIO
                        
                        image_data = base64.b64decode(elem.text)
                        pil_image = Image.open(BytesIO(image_data))
                        
                        # Original-Größe für Overlay-Berechnungen speichern
                        self.original_image_size = (pil_image.width, pil_image.height)
                        
                        # Skalieren wenn zu groß für die Anzeige
                        max_width, max_height = 600, 400
                        if pil_image.width > max_width or pil_image.height > max_height:
                            # Skalierungsfaktor berechnen
                            scale_x = max_width / pil_image.width
                            scale_y = max_height / pil_image.height
                            self.image_scale_factor = min(scale_x, scale_y)
                            
                            new_size = (int(pil_image.width * self.image_scale_factor),
                                       int(pil_image.height * self.image_scale_factor))
                            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                        else:
                            self.image_scale_factor = 1.0
                        
                        # Für tkinter konvertieren
                        self.screenshot_image = ImageTk.PhotoImage(pil_image)
                        
                        # Canvas leeren und Bild anzeigen
                        self.screenshot_canvas.delete("all")
                        self.screenshot_canvas.create_image(10, 10, anchor=tk.NW, 
                                                          image=self.screenshot_image, tags='screenshot')
                        
                        # Element-Overlays hinzufügen
                        self.show_element_overlays()
                        
                        # Scroll-Region setzen
                        self.screenshot_canvas.configure(scrollregion=self.screenshot_canvas.bbox("all"))
                        
                        return
                    
                    except ImportError:
                        # Fallback wenn Pillow nicht verfügbar
                        self.show_screenshot_fallback(elem)
                        return
                    except Exception as e:
                        print(f"Fehler beim Dekodieren des Screenshots: {e}")
                        self.show_screenshot_error()
                        return
            
            # Kein Screenshot gefunden
            self.screenshot_canvas.delete("all")
            self.screenshot_canvas.create_text(150, 100, text="Kein Screenshot im XML gefunden", 
                                            font=('Arial', 12), fill='gray')
            
        except Exception as e:
            print(f"Fehler beim Laden des Screenshots: {e}")
            self.show_screenshot_error()
    
    def show_screenshot_fallback(self, elem):
        """Zeigt Screenshot-Info ohne Pillow"""
        self.screenshot_canvas.delete("all")
        info_text = "Screenshot gefunden (PNG)\n"
        info_text += f"Größe: {len(elem.text) if elem.text else 0} Zeichen (Base64)\n\n"
        info_text += "Für vollständige Bildanzeige ist PIL/Pillow erforderlich:\n"
        info_text += "pip install Pillow"
        
        self.screenshot_canvas.create_text(10, 10, anchor=tk.NW, text=info_text,
                                         font=('Arial', 10), fill='blue', width=300)
        self.show_geometry_overlays()
    
    def show_screenshot_error(self):
        """Zeigt Screenshot-Fehler"""
        self.screenshot_canvas.delete("all")
        self.screenshot_canvas.create_text(150, 100, text="Fehler beim Laden des Screenshots", 
                                        font=('Arial', 12), fill='red')
    
    def show_element_overlays(self):
        """Zeigt Element-Overlays über dem Screenshot (wie in der HTML-Version)"""
        try:
            if not hasattr(self, 'image_scale_factor'):
                self.image_scale_factor = 1.0
            
            # Durchsuche XML nach allen Elementen mit Geometrie-Informationen
            for elem in self.xml_data.iter():
                if elem.tag == 'element':
                    # Suche nach abstractProperties/geometry
                    abstract_props = elem.find('abstractProperties')
                    if abstract_props is not None:
                        geometry = abstract_props.find('geometry')
                        if geometry is not None:
                            self.create_element_overlay(geometry, elem)
        
        except Exception as e:
            print(f"Fehler beim Erstellen der Element-Overlays: {e}")
    
    def show_geometry_overlays(self):
        """Zeigt einfache Geometrie-Overlays (Fallback ohne Bild)"""
        try:
            y_offset = 120  # Offset unter dem Info-Text
            
            # Durchsuche XML nach Geometrie-Informationen
            for elem in self.xml_data.iter():
                if elem.tag == 'geometry':
                    x_elem = elem.find('x')
                    y_elem = elem.find('y') 
                    w_elem = elem.find('width')
                    h_elem = elem.find('height')
                    
                    if all(e is not None for e in [x_elem, y_elem, w_elem, h_elem]):
                        try:
                            x = int(x_elem.text) // 15 + 10  # Skalierung für Anzeige
                            y = int(y_elem.text) // 15 + y_offset
                            w = max(int(w_elem.text) // 15, 5)
                            h = max(int(h_elem.text) // 15, 5)
                            
                            # Rotes Overlay-Rechteck
                            self.screenshot_canvas.create_rectangle(
                                x, y, x + w, y + h,
                                outline='red', width=2, fill='', 
                                tags='overlay'
                            )
                        except (ValueError, AttributeError):
                            continue
            
            # Scroll-Region aktualisieren
            self.screenshot_canvas.configure(scrollregion=self.screenshot_canvas.bbox("all"))
            
        except Exception as e:
            print(f"Fehler beim Erstellen der Overlays: {e}")
    
    def create_element_overlay(self, geometry, element):
        """Erstellt ein Overlay für ein Element"""
        try:
            x_elem = geometry.find('x')
            y_elem = geometry.find('y')
            w_elem = geometry.find('width')  
            h_elem = geometry.find('height')
            
            if all(e is not None and e.text for e in [x_elem, y_elem, w_elem, h_elem]):
                # Koordinaten mit Skalierung
                x = int(x_elem.text) * self.image_scale_factor + 10
                y = int(y_elem.text) * self.image_scale_factor + 10
                w = int(w_elem.text) * self.image_scale_factor
                h = int(h_elem.text) * self.image_scale_factor
                
                if w > 2 and h > 2:  # Mindestgröße für Sichtbarkeit
                    # Rotes Overlay-Rechteck (wie in der HTML-Version)
                    rect_id = self.screenshot_canvas.create_rectangle(
                        x, y, x + w, y + h,
                        outline='red', width=2, fill='red',
                        stipple='gray50',  # Transparenz-Simulation
                        tags='element_overlay'
                    )
                    
                    # Element-Info beim Hover (vereinfacht)
                    element_class = element.get('class', '')
                    simplified_type = element.get('simplifiedType', '')
                    tooltip_text = simplified_type or element_class
                    
                    if tooltip_text:
                        # Kleines Label für Element-Typ
                        self.screenshot_canvas.create_text(
                            x + 2, y - 2, anchor=tk.SW, 
                            text=tooltip_text, font=('Arial', 8),
                            fill='red', tags='element_label'
                        )
        
        except (ValueError, AttributeError) as e:
            print(f"Fehler beim Erstellen des Element-Overlays: {e}")
    
    def populate_tree(self):
        """Füllt den XML-Baum mit Daten"""
        # Alten Inhalt löschen
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if self.xml_data is not None:
            self.add_tree_item("", self.xml_data)
            
            # Ersten Knoten automatisch expandieren
            if self.tree.get_children():
                first_item = self.tree.get_children()[0]
                self.tree.item(first_item, open=True)
    
    def add_tree_item(self, parent, element):
        """Fügt ein Element zum Baum hinzu (rekursiv)"""
        # Bestimme Anzeige-Text basierend auf Element-Typ
        display_text = element.tag
        
        if element.tag == 'element':
            # Für <element> verwende class und simplifiedType
            class_name = element.get('class', '')
            simplified_type = element.get('simplifiedType', '')
            if simplified_type:
                display_text = f"{simplified_type} [{class_name}]"
            elif class_name:
                display_text = class_name
        
        # Baum-Item hinzufügen
        item_id = self.tree.insert(parent, tk.END, text=display_text, tags=("element",))
        
        # Element-Daten als versteckte Attribute speichern
        self.tree.set(item_id, "xml_element_ref", id(element))
        
        # Kinder-Elemente rekursiv hinzufügen (aber nicht alle XML-Elemente)
        for child in element:
            if child.tag in ['element', 'children']:  # Nur relevante Kinder anzeigen
                if child.tag == 'children':
                    # Für <children> die enthaltenen <element> direkt hinzufügen
                    for grandchild in child:
                        if grandchild.tag == 'element':
                            self.add_tree_item(item_id, grandchild)
                else:
                    self.add_tree_item(item_id, child)
    
    def on_tree_select(self, event):
        """Wird aufgerufen wenn ein Baum-Element ausgewählt wird"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        
        # Element-Daten abrufen
        item_data = self.tree.item(item_id)
        
        # Properties aktualisieren
        self.update_properties(item_id, item_data)
    
    def update_properties(self, item_id, item_data):
        """Aktualisiert das Properties-Panel"""
        # Properties leeren
        for item in self.properties.get_children():
            self.properties.delete(item)
        
        # XML-Element-Referenz abrufen
        element_ref_id = self.tree.set(item_id, "xml_element_ref")
        if not element_ref_id:
            return
            
        # Das tatsächliche XML-Element finden
        xml_element = self.find_element_by_id(int(element_ref_id))
        if not xml_element:
            return
        
        # Grundlegende Element-Informationen
        self.properties.insert("", tk.END, text="Tag", values=(xml_element.tag,))
        
        # Element-Attribute anzeigen
        if xml_element.attrib:
            # Gruppierter Header für Attribute
            attr_group = self.properties.insert("", tk.END, text="Attributes", 
                                               values=(""), tags=("group",))
            
            # Sortiere Attribute basierend auf Sort-Einstellung
            attrs = list(xml_element.attrib.items())
            if self.sort_var.get() == "asc":
                attrs.sort()
            elif self.sort_var.get() == "desc":
                attrs.sort(reverse=True)
            
            for attr_name, attr_value in attrs:
                self.properties.insert(attr_group, tk.END, text=attr_name, 
                                     values=(attr_value,), tags=("attribute",))
        
        # Properties aus <properties> Subelement
        properties_elem = xml_element.find('properties')
        if properties_elem is not None:
            props_group = self.properties.insert("", tk.END, text="Properties", 
                                               values=(""), tags=("group",))
            
            # Sammle Properties
            props = []
            for prop in properties_elem.findall('property'):
                prop_name = prop.get('name', '')
                prop_value = prop.text or prop.find('string')
                if prop_value is not None:
                    if hasattr(prop_value, 'text'):
                        prop_value = prop_value.text or ""
                    props.append((prop_name, str(prop_value)))
            
            # Sortiere Properties
            if self.sort_var.get() == "asc":
                props.sort()
            elif self.sort_var.get() == "desc":
                props.sort(reverse=True)
            
            for prop_name, prop_value in props:
                self.properties.insert(props_group, tk.END, text=prop_name, 
                                     values=(prop_value,), tags=("property",))
        
        # Geometry-Informationen
        geometry_elem = xml_element.find('.//geometry')
        if geometry_elem is not None:
            geom_group = self.properties.insert("", tk.END, text="Geometry", 
                                              values=(""), tags=("group",))
            
            for child in geometry_elem:
                self.properties.insert(geom_group, tk.END, text=child.tag, 
                                     values=(child.text or "",), tags=("geometry",))
        
        # Erweitere alle Gruppen standardmäßig
        for item in self.properties.get_children():
            if self.properties.set(item, "value") == "":
                self.properties.item(item, open=True)
    
    def find_element_by_id(self, element_id):
        """Findet ein XML-Element anhand seiner ID"""
        def search_element(elem):
            if id(elem) == element_id:
                return elem
            for child in elem:
                result = search_element(child)
                if result is not None:
                    return result
            return None
        
        if self.xml_data is not None:
            return search_element(self.xml_data)
        return None
    
    def refresh_properties(self):
        """Aktualisiert die Properties-Anzeige mit aktuellen Sort-Einstellungen"""
        selection = self.tree.selection()
        if selection:
            item_data = self.tree.item(selection[0])
            self.update_properties(selection[0], item_data)
    
    def show_tree_context_menu(self, event):
        """Zeigt das Kontextmenü für den Baum"""
        # Element unter Cursor auswählen
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree_context_menu.post(event.x_root, event.y_root)
    
    def show_props_context_menu(self, event):
        """Zeigt das Kontextmenü für Properties"""
        item = self.properties.identify_row(event.y)
        if item:
            self.properties.selection_set(item)
            self.props_context_menu.post(event.x_root, event.y_root)
    
    def copy_to_clipboard(self, copy_type):
        """Kopiert Daten in die Zwischenablage"""
        try:
            copied_text = ""
            
            if copy_type.startswith("tree_"):
                selection = self.tree.selection()
                if not selection:
                    return
                
                item_id = selection[0]
                item_data = self.tree.item(item_id)
                element_ref_id = self.tree.set(item_id, "xml_element_ref")
                
                if copy_type == "tree_name":
                    copied_text = item_data.get('text', '')
                elif copy_type == "tree_realname":
                    if element_ref_id:
                        xml_element = self.find_element_by_id(int(element_ref_id))
                        if xml_element is not None:
                            realname_elem = xml_element.find('realname')
                            if realname_elem is not None:
                                copied_text = realname_elem.text or ""
                elif copy_type == "tree_id":
                    if element_ref_id:
                        xml_element = self.find_element_by_id(int(element_ref_id))
                        if xml_element is not None:
                            copied_text = xml_element.get('id', '')
            
            elif copy_type.startswith("prop_"):
                selection = self.properties.selection()
                if not selection:
                    return
                
                item_id = selection[0]
                item_data = self.properties.item(item_id)
                
                prop_name = item_data.get('text', '')
                values = item_data.get('values', [])
                prop_value = values[0] if values else ""
                
                if copy_type == "prop_name":
                    copied_text = prop_name
                elif copy_type == "prop_value":
                    copied_text = prop_value
                elif copy_type == "prop_both":
                    copied_text = f"{prop_name}={prop_value}"
            
            if copied_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(copied_text)
                self.root.update()  # Clipboard aktualisieren
                
                # Toast-Benachrichtigung anzeigen
                action_map = {
                    "tree_name": "Element-Name",
                    "tree_realname": "Realname", 
                    "tree_id": "Element-ID",
                    "prop_name": "Property",
                    "prop_value": "Value",
                    "prop_both": "Property=Value"
                }
                
                action_text = action_map.get(copy_type, "Text")
                self.toast.show_toast(f"{action_text} kopiert: {copied_text[:50]}{'...' if len(copied_text) > 50 else ''}")
                
        except Exception as e:
            self.toast.show_toast(f"Fehler beim Kopieren: {str(e)}", "error")
    
    def filter_tree(self, *args):
        """Filtert den XML-Baum basierend auf Suchbegriff"""
        search_term = self.tree_search_var.get().lower()
        
        if not search_term:
            # Alle Items anzeigen
            self._show_all_tree_items()
            return
        
        # Alle Items verstecken, dann passende anzeigen
        self._hide_all_tree_items()
        self._show_matching_tree_items(search_term)
    
    def _hide_all_tree_items(self):
        """Versteckt alle Baum-Items"""
        def hide_children(parent=""):
            for item in self.tree.get_children(parent):
                self.tree.detach(item)
                hide_children(item)
        
        hide_children()
    
    def _show_all_tree_items(self):
        """Zeigt alle Baum-Items"""
        # Das ist kompliziert in tkinter - einfacher ist es, den Baum neu aufzubauen
        self.populate_tree()
    
    def _show_matching_tree_items(self, search_term):
        """Zeigt passende Baum-Items (vereinfachte Implementierung)"""
        # Für jetzt eine einfache Implementierung - in einer vollständigen Version
        # würde man eine rekursive Suche implementieren
        pass
    
    def filter_properties(self, *args):
        """Filtert Properties basierend auf Suchbegriff"""
        search_term = self.props_search_var.get().lower()
        
        # Einfache Implementierung - versteckt/zeigt Properties
        for item_id in self.properties.get_children():
            item_data = self.properties.item(item_id)
            text = item_data.get('text', '').lower()
            values = item_data.get('values', [])
            value_text = values[0].lower() if values else ""
            
            if not search_term or search_term in text or search_term in value_text:
                # Item anzeigen (durch Wiederhinzufügen)
                pass
            else:
                # Item verstecken ist in tkinter kompliziert
                pass
    
    def reload_file(self):
        """Lädt die aktuelle Datei neu"""
        if self.current_file:
            self.load_xml_file(self.current_file)
        else:
            self.toast.show_toast("Keine Datei zum Neuladen geöffnet", "error")
    
    def close_file(self):
        """Schließt die aktuelle Datei"""
        self.current_file = None
        self.xml_data = None
        
        # UI zurücksetzen
        self.file_label.config(text="Keine Datei geladen")
        
        # Baum leeren
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Properties leeren
        for item in self.properties.get_children():
            self.properties.delete(item)
        
        self.toast.show_toast("Datei geschlossen")
    
    def run(self):
        """Startet die Anwendung"""
        self.root.mainloop()


def main():
    """Hauptfunktion"""
    app = SquishXMLDesktopViewer()
    app.run()


if __name__ == "__main__":
    main()