#!/usr/bin/env python3
"""
squish_xml_console.py

Konsolen-Version des Squish XML Viewers mit allen Features
- Funktioniert garantiert ohne externe Abhängigkeiten
- Interactive Console Interface
- Alle Funktionen der Web-Version
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json

class ConsoleXMLViewer:
    """Konsolen-Version des XML Viewers"""
    
    def __init__(self):
        self.current_file = None
        self.xml_data = None
        self.current_element = None
        self.history = []
        
        print("🚀 Squish XML Snapshot Viewer (Console Edition)")
        print("=" * 50)
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
        
        self.main_loop()
    
    def main_loop(self):
        """Haupt-Schleife für Benutzerinteraktion"""
        while True:
            try:
                print("\n" + "─" * 50)
                if self.current_file:
                    print(f"📄 Datei: {os.path.basename(self.current_file)}")
                else:
                    print("📄 Keine Datei geladen")
                
                print("\n📋 Verfügbare Kommandos:")
                print("  1 - Datei öffnen")
                print("  2 - XML-Struktur anzeigen") 
                print("  3 - Element-Details anzeigen")
                print("  4 - Suchen")
                print("  5 - Eigenschaften kopieren")
                print("  r - Datei neu laden")
                print("  q - Beenden")
                
                choice = input("\n➤ Wählen Sie ein Kommando: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == '1':
                    self.open_file_interactive()
                elif choice == '2':
                    self.show_xml_structure()
                elif choice == '3':
                    self.show_element_details()
                elif choice == '4':
                    self.search_elements()
                elif choice == '5':
                    self.copy_properties()
                elif choice == 'r':
                    self.reload_file()
                else:
                    print("❌ Ungültiges Kommando!")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Auf Wiedersehen!")
                break
            except Exception as e:
                print(f"❌ Fehler: {e}")
    
    def open_file_interactive(self):
        """Interaktives Öffnen einer Datei"""
        print("\n📁 Datei öffnen")
        print("Geben Sie den Pfad zur XML-Datei ein:")
        file_path = input("➤ ").strip()
        
        if file_path and os.path.exists(file_path):
            if file_path.lower().endswith('.xml'):
                self.load_xml_file(file_path)
            else:
                print("❌ Bitte wählen Sie eine XML-Datei!")
        else:
            print("❌ Datei nicht gefunden!")
    
    def load_xml_file(self, file_path):
        """XML-Datei laden"""
        try:
            print(f"⏳ Lade {file_path}...")
            
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            self.current_file = file_path
            
            print(f"✅ XML-Datei erfolgreich geladen!")
            print(f"📊 Root-Element: {self.xml_data.tag}")
            
            # Statistiken
            all_elements = self.xml_data.iter()
            element_count = sum(1 for _ in all_elements)
            
            self.xml_data_iter = self.xml_data.iter()  # Neu erstellen da Iterator verbraucht
            attribute_count = sum(len(elem.attrib) for elem in self.xml_data.iter())
            
            print(f"📈 Statistiken:")
            print(f"   • Elemente: {element_count}")
            print(f"   • Attribute: {attribute_count}")
            
        except Exception as e:
            print(f"❌ Fehler beim Laden: {e}")
    
    def show_xml_structure(self):
        """XML-Struktur anzeigen"""
        if not self.xml_data:
            print("❌ Keine XML-Datei geladen!")
            return
        
        print("\n🌳 XML-Struktur:")
        print("=" * 30)
        
        max_depth = input("➤ Maximale Tiefe (Enter für alle): ").strip()
        max_depth = int(max_depth) if max_depth.isdigit() else None
        
        self.print_element(self.xml_data, 0, max_depth)
    
    def print_element(self, element, depth, max_depth=None):
        """Element rekursiv ausgeben"""
        if max_depth is not None and depth > max_depth:
            return
        
        indent = "  " * depth
        icon = "📁" if list(element) else "📄"
        
        # Element-Info
        text_preview = ""
        if element.text and element.text.strip():
            text_preview = f" 💬 '{element.text.strip()[:30]}{'...' if len(element.text.strip()) > 30 else ''}'"
        
        print(f"{indent}{icon} {element.tag}{text_preview}")
        
        # Attribute
        if element.attrib:
            for attr_name, attr_value in element.attrib.items():
                print(f"{indent}  🏷️  @{attr_name} = '{attr_value}'")
        
        # Kinder
        for child in element:
            self.print_element(child, depth + 1, max_depth)
    
    def show_element_details(self):
        """Details für ein bestimmtes Element anzeigen"""
        if not self.xml_data:
            print("❌ Keine XML-Datei geladen!")
            return
        
        print("\n🔍 Element-Details")
        element_name = input("➤ Element-Name (oder leer für Root): ").strip()
        
        if not element_name:
            target_element = self.xml_data
        else:
            # Element suchen
            target_element = None
            for elem in self.xml_data.iter():
                if elem.tag == element_name:
                    target_element = elem
                    break
            
            if not target_element:
                print(f"❌ Element '{element_name}' nicht gefunden!")
                return
        
        self.display_element_properties(target_element)
    
    def display_element_properties(self, element):
        """Element-Eigenschaften detailliert anzeigen"""
        print(f"\n📋 Details für Element: {element.tag}")
        print("=" * 40)
        
        # Basis-Informationen
        print(f"🏷️  Name: {element.tag}")
        print(f"🔖 Typ: element")
        
        if element.text and element.text.strip():
            print(f"💬 Text: {element.text.strip()}")
        
        # Attribute
        if element.attrib:
            print(f"\n🏷️  Attribute ({len(element.attrib)}):")
            for attr_name, attr_value in element.attrib.items():
                print(f"   • {attr_name} = '{attr_value}'")
        
        # Kinder-Elemente
        children = list(element)
        if children:
            print(f"\n👶 Kinder-Elemente ({len(children)}):")
            for child in children[:10]:  # Erste 10 anzeigen
                text_preview = ""
                if child.text and child.text.strip():
                    text_preview = f" - '{child.text.strip()[:20]}...'"
                print(f"   • {child.tag}{text_preview}")
            
            if len(children) > 10:
                print(f"   ... und {len(children) - 10} weitere")
        
        # Parent-Element
        parent = self.find_parent(element)
        if parent is not None:
            print(f"\n👨‍👩‍👧‍👦 Parent: {parent.tag}")
        
        # Pfad
        path = self.get_element_path(element)
        print(f"\n🗂️  XML-Pfad: {path}")
    
    def find_parent(self, target_element):
        """Parent-Element finden"""
        for elem in self.xml_data.iter():
            if target_element in list(elem):
                return elem
        return None
    
    def get_element_path(self, target_element):
        """XML-Pfad für Element erstellen"""
        path_parts = []
        
        def find_path(element, current_path):
            current_path = current_path + [element.tag]
            
            if element == target_element:
                path_parts.extend(current_path)
                return True
            
            for child in element:
                if find_path(child, current_path):
                    return True
            
            return False
        
        find_path(self.xml_data, [])
        return "/" + "/".join(path_parts) if path_parts else "/unknown"
    
    def search_elements(self):
        """In XML-Elementen suchen"""
        if not self.xml_data:
            print("❌ Keine XML-Datei geladen!")
            return
        
        print("\n🔍 In XML suchen")
        search_term = input("➤ Suchbegriff: ").strip().lower()
        
        if not search_term:
            return
        
        print(f"\n🔍 Suchergebnisse für '{search_term}':")
        print("=" * 40)
        
        results = []
        
        # In Element-Namen suchen
        for elem in self.xml_data.iter():
            if search_term in elem.tag.lower():
                results.append(("Element-Name", elem.tag, elem))
            
            # In Attributen suchen
            for attr_name, attr_value in elem.attrib.items():
                if search_term in attr_name.lower() or search_term in attr_value.lower():
                    results.append(("Attribut", f"{attr_name}='{attr_value}'", elem))
            
            # In Text suchen
            if elem.text and search_term in elem.text.lower():
                results.append(("Text", elem.text.strip()[:50], elem))
        
        if results:
            for i, (match_type, match_value, element) in enumerate(results[:20], 1):
                print(f"{i:2d}. [{match_type}] {match_value}")
                print(f"     in Element: {element.tag}")
            
            if len(results) > 20:
                print(f"\n... und {len(results) - 20} weitere Treffer")
            
            # Element-Details anzeigen
            try:
                choice = input(f"\n➤ Element-Details anzeigen (1-{min(len(results), 20)}) oder Enter: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= min(len(results), 20):
                    selected_element = results[int(choice) - 1][2]
                    self.display_element_properties(selected_element)
            except:
                pass
        else:
            print("❌ Keine Treffer gefunden!")
    
    def copy_properties(self):
        """Eigenschaften in 'Zwischenablage' (Datei) kopieren"""
        if not self.xml_data:
            print("❌ Keine XML-Datei geladen!")
            return
        
        print("\n📋 Eigenschaften kopieren")
        element_name = input("➤ Element-Name (oder leer für Root): ").strip()
        
        if not element_name:
            target_element = self.xml_data
        else:
            # Element suchen
            target_element = None
            for elem in self.xml_data.iter():
                if elem.tag == element_name:
                    target_element = elem
                    break
            
            if not target_element:
                print(f"❌ Element '{element_name}' nicht gefunden!")
                return
        
        # Eigenschaften sammeln
        properties = []
        properties.append(f"Element: {target_element.tag}")
        
        if target_element.text and target_element.text.strip():
            properties.append(f"Text: {target_element.text.strip()}")
        
        if target_element.attrib:
            properties.append("Attribute:")
            for attr_name, attr_value in target_element.attrib.items():
                properties.append(f"  {attr_name} = {attr_value}")
        
        properties_text = "\\n".join(properties)
        
        # In Datei schreiben (simuliert Zwischenablage)
        try:
            with open("clipboard.txt", "w", encoding="utf-8") as f:
                f.write(properties_text)
            
            print("✅ Eigenschaften in 'clipboard.txt' gespeichert!")
            print("📄 Inhalt:")
            for prop in properties:
                print(f"   {prop}")
        except Exception as e:
            print(f"❌ Fehler beim Kopieren: {e}")
    
    def reload_file(self):
        """Aktuelle Datei neu laden"""
        if self.current_file:
            self.load_xml_file(self.current_file)
        else:
            print("❌ Keine Datei zum Neuladen!")

def main():
    """Hauptfunktion"""
    ConsoleXMLViewer()

if __name__ == "__main__":
    main()