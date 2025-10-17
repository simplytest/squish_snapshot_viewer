#!/usr/bin/env python3
"""
Einfacher Squish XML Viewer - Pure Python ohne externe Abhängigkeiten
Funktioniert mit der Python-Standardbibliothek
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Versuche tkinter zu importieren, fallback zu print-basierter Ausgabe
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("Tkinter nicht verfügbar - verwende Konsolen-Modus")

class SimpleXMLViewer:
    """Einfacher XML Viewer - funktioniert mit oder ohne tkinter"""
    
    def __init__(self):
        self.current_file = None
        self.xml_data = None
        
        if TKINTER_AVAILABLE:
            self.create_gui()
        else:
            self.console_mode()
    
    def create_gui(self):
        """Erstelle einfache GUI mit tkinter"""
        self.root = tk.Tk()
        self.root.title("Squish XML Viewer")
        self.root.geometry("1000x700")
        
        # Menü
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Öffnen", command=self.open_file)
        file_menu.add_command(label="Beenden", command=self.root.quit)
        
        # Haupt-Frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Info-Label
        self.info_label = ttk.Label(main_frame, text="Bitte XML-Datei öffnen")
        self.info_label.pack(pady=5)
        
        # Button zum Öffnen
        open_btn = ttk.Button(main_frame, text="XML-Datei öffnen", command=self.open_file)
        open_btn.pack(pady=5)
        
        # Text-Widget für XML-Inhalt
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
    
    def open_file(self):
        """Datei-Dialog öffnen"""
        if not TKINTER_AVAILABLE:
            return
        
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
        """XML-Datei laden und anzeigen"""
        try:
            self.current_file = file_path
            
            # XML parsen
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            
            if TKINTER_AVAILABLE:
                # GUI aktualisieren
                self.info_label.config(text=f"Datei: {os.path.basename(file_path)}")
                
                # XML-Inhalt formatiert anzeigen
                formatted_content = self.format_xml_element(self.xml_data, 0)
                
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, formatted_content)
                
                messagebox.showinfo("Erfolg", f"XML-Datei '{os.path.basename(file_path)}' erfolgreich geladen!")
            else:
                # Konsolen-Ausgabe
                print(f"\n=== XML-Datei: {os.path.basename(file_path)} ===")
                print(self.format_xml_element(self.xml_data, 0))
                
        except Exception as e:
            error_msg = f"Fehler beim Laden der XML-Datei: {str(e)}"
            if TKINTER_AVAILABLE:
                messagebox.showerror("Fehler", error_msg)
            else:
                print(f"FEHLER: {error_msg}")
    
    def format_xml_element(self, element, indent_level):
        """Formatiert XML-Element für Anzeige"""
        indent = "  " * indent_level
        result = []
        
        # Element-Name
        element_line = f"{indent}📁 {element.tag}"
        
        # Attribute
        if element.attrib:
            attrs = ", ".join([f"{k}='{v}'" for k, v in element.attrib.items()])
            element_line += f" [{attrs}]"
        
        result.append(element_line)
        
        # Text-Inhalt
        if element.text and element.text.strip():
            result.append(f"{indent}  💬 Text: {element.text.strip()}")
        
        # Kinder-Elemente
        for child in element:
            result.append(self.format_xml_element(child, indent_level + 1))
        
        return "\n".join(result)
    
    def console_mode(self):
        """Konsolen-Modus wenn tkinter nicht verfügbar"""
        print("=== Squish XML Viewer (Konsolen-Modus) ===")
        
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            # Datei aus Argument laden
            self.load_xml_file(sys.argv[1])
        else:
            # Nach Datei fragen
            while True:
                file_path = input("\nBitte geben Sie den Pfad zur XML-Datei ein (oder 'quit' zum Beenden): ").strip()
                
                if file_path.lower() == 'quit':
                    break
                
                if os.path.exists(file_path) and file_path.endswith('.xml'):
                    self.load_xml_file(file_path)
                    
                    # Frage nach weiterer Datei
                    continue_input = input("\nWeitere Datei laden? (j/n): ").strip().lower()
                    if continue_input != 'j':
                        break
                else:
                    print("Datei nicht gefunden oder keine XML-Datei!")
    
    def run(self):
        """Anwendung starten"""
        if TKINTER_AVAILABLE:
            self.root.mainloop()
        # Konsolen-Modus läuft bereits in __init__

def main():
    """Hauptfunktion"""
    print("Starte Squish XML Viewer...")
    
    viewer = SimpleXMLViewer()
    viewer.run()
    
    print("Viewer beendet.")

if __name__ == "__main__":
    main()