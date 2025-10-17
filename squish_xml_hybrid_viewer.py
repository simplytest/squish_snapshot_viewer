#!/usr/bin/env python3
"""
squish_xml_hybrid_viewer.py

Hybride Desktop-App für Squish XML Viewer
- Python: File-Handling, Ordner-Management, HTML-Generierung
- WebView: Anzeige der generierten HTML-Datei (nutzt die perfekt funktionierende HTML-Version)

Layout:
- Oben: Menüleiste 
- Links: Datei-Liste (XML-Dateien)
- Rechts: WebView mit generierter HTML-Datei
"""

import sys
import os
import xml.etree.ElementTree as ET
import base64
import tempfile
import json
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTreeWidget, QTreeWidgetItem, QSplitter, QMenu, QAction, 
        QFileDialog, QMessageBox, QLabel, QFrame, QPushButton,
        QListWidget, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, QUrl, pyqtSignal
    from PyQt5.QtGui import QFont, QIcon
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class SquishXMLHybridViewer(QMainWindow):
    """Hybride XML-Viewer App - Python + WebView"""
    
    def __init__(self):
        super().__init__()
        
        if not PYQT_AVAILABLE:
            print("❌ PyQt5 und QWebEngineWidgets nicht verfügbar!")
            print("Installieren Sie: pip install PyQt5 PyQtWebEngine")
            sys.exit(1)
        
        self.xml_files = []  # Liste der geladenen XML-Dateien
        self.current_xml_file = None
        self.temp_html_file = None
        
        self.init_ui()
        
        # Falls Datei/Ordner als Argument übergeben
        if len(sys.argv) > 1:
            path = sys.argv[1]
            if os.path.isfile(path) and path.endswith('.xml'):
                self.load_xml_file(path)
            elif os.path.isdir(path):
                self.load_xml_folder(path)
    
    def init_ui(self):
        """UI erstellen - Hybrid-Layout"""
        self.setWindowTitle("Squish XML Hybrid Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Menüleiste erstellen
        self.create_menu()
        
        # Horizontal Splitter: Links Dateiliste, Rechts WebView
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Links: Dateiliste
        self.create_file_list_panel(splitter)
        
        # Rechts: WebView 
        self.create_webview_panel(splitter)
        
        # Splitter-Verhältnisse: 300px links, Rest rechts
        splitter.setSizes([300, 1100])
        
        # Statusleiste
        self.statusBar().showMessage("Bereit - Datei oder Ordner öffnen")
    
    def create_menu(self):
        """Menüleiste erstellen"""
        menubar = self.menuBar()
        
        # macOS: Native Menüleiste verwenden (oben in der Systemleiste)
        menubar.setNativeMenuBar(True)
        
        # Datei-Menü
        file_menu = menubar.addMenu('&Datei')
        
        # XML-Datei öffnen
        open_file_action = QAction('&XML-Datei öffnen...', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.triggered.connect(self.open_xml_file)
        file_menu.addAction(open_file_action)
        
        # Ordner öffnen
        open_folder_action = QAction('&Ordner öffnen...', self)
        open_folder_action.setShortcut('Ctrl+Shift+O')
        open_folder_action.triggered.connect(self.open_xml_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Liste leeren
        clear_action = QAction('Liste &leeren', self)
        clear_action.setShortcut('Ctrl+L')
        clear_action.triggered.connect(self.clear_file_list)
        file_menu.addAction(clear_action)
        
        file_menu.addSeparator()
        
        # Beenden
        exit_action = QAction('&Beenden', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Ansicht-Menü
        view_menu = menubar.addMenu('&Ansicht')
        
        # WebView neu laden
        reload_action = QAction('WebView &neu laden', self)
        reload_action.setShortcut('F5')
        reload_action.triggered.connect(self.reload_webview)
        view_menu.addAction(reload_action)
        
        # HTML-Datei im Browser öffnen
        open_browser_action = QAction('In &Browser öffnen', self)
        open_browser_action.setShortcut('Ctrl+B')
        open_browser_action.triggered.connect(self.open_in_browser)
        view_menu.addAction(open_browser_action)
        
        # Hilfe-Menü
        help_menu = menubar.addMenu('&Hilfe')
        
        # Über
        about_action = QAction('&Über Squish XML Viewer', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_file_list_panel(self, parent_splitter):
        """Dateiliste-Panel erstellen (links)"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f6f8fa;
                border-right: 1px solid #e1e4e8;
            }
        """)
        parent_splitter.addWidget(panel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("XML-Dateien")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #24292e;
            padding: 8px 0;
            border-bottom: 1px solid #e1e4e8;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Dateiliste
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e1e4e8;
                background-color: white;
                font-size: 14px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f6f8fa;
            }
            QListWidget::item:selected {
                background-color: #0366d6;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #f1f8ff;
            }
        """)
        self.file_list.itemClicked.connect(self.on_file_selected)
        layout.addWidget(self.file_list)
        
        # Info-Text für leere Liste
        self.info_label = QLabel("Keine XML-Dateien geladen.\n\nVerwenden Sie das Datei-Menü zum Öffnen von:\n• XML-Dateien (Strg+O)\n• Ordnern (Strg+Shift+O)")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #586069;
                font-size: 12px;
                padding: 20px;
                text-align: center;
                background-color: #f8f9fa;
                border: 1px dashed #dee2e6;
                border-radius: 4px;
                margin: 10px 0;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
    
    def create_webview_panel(self, parent_splitter):
        """WebView-Panel erstellen (rechts)"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        parent_splitter.addWidget(panel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # WebView
        self.webview = QWebEngineView()
        self.webview.setStyleSheet("border: none;")
        
        # Standard-Seite laden (Willkommensseite)
        self.load_welcome_page()
        
        layout.addWidget(self.webview)
    
    def load_welcome_page(self):
        """Willkommensseite laden"""
        welcome_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Squish XML Hybrid Viewer</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    color: white;
                }
                .welcome-container {
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 60px 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    font-size: 3em;
                    margin-bottom: 20px;
                    font-weight: 300;
                }
                .subtitle {
                    font-size: 1.2em;
                    margin-bottom: 40px;
                    opacity: 0.9;
                }
                .feature {
                    margin: 15px 0;
                    font-size: 1.1em;
                }
                .icon {
                    font-size: 2em;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="welcome-container">
                <div class="icon">🔍</div>
                <h1>Squish XML Hybrid Viewer</h1>
                <div class="subtitle">Moderne Hybride Anwendung</div>
                
                <div class="feature">📄 XML-Datei öffnen (Ctrl+O)</div>
                <div class="feature">📁 Ordner öffnen (Ctrl+Shift+O)</div>
                <div class="feature">🌐 HTML-Darstellung mit WebView</div>
                <div class="feature">🔍 Element-Overlays und Navigation</div>
                
                <br><br>
                <div style="opacity: 0.7; font-size: 0.9em;">
                    Wählen Sie eine XML-Datei aus der Liste links<br>
                    oder nutzen Sie das Datei-Menü
                </div>
            </div>
        </body>
        </html>
        """
        
        self.webview.setHtml(welcome_html)
    
    def open_xml_file(self):
        """XML-Datei öffnen Dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "XML-Datei öffnen", 
            "", 
            "XML Files (*.xml);;All Files (*)"
        )
        if file_path:
            self.load_xml_file(file_path)
    
    def open_xml_folder(self):
        """XML-Ordner öffnen Dialog"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Ordner mit XML-Dateien öffnen"
        )
        if folder_path:
            self.load_xml_folder(folder_path)
    
    def load_xml_file(self, file_path):
        """Einzelne XML-Datei zur Liste hinzufügen"""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Fehler", f"Datei nicht gefunden: {file_path}")
            return
        
        # Prüfen ob schon in der Liste
        for xml_file in self.xml_files:
            if xml_file['path'] == file_path:
                self.select_file_in_list(file_path)
                return
        
        # Zur Liste hinzufügen
        xml_file = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path)
        }
        self.xml_files.append(xml_file)
        
        # Liste aktualisieren
        self.update_file_list()
        
        # Datei automatisch auswählen
        self.select_file_in_list(file_path)
        
        self.statusBar().showMessage(f"XML-Datei hinzugefügt: {xml_file['name']}")
    
    def load_xml_folder(self, folder_path):
        """Alle XML-Dateien aus Ordner laden"""
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, "Fehler", f"Ordner nicht gefunden: {folder_path}")
            return
        
        xml_files_found = []
        
        # Alle XML-Dateien im Ordner finden
        for file_name in os.listdir(folder_path):
            if file_name.lower().endswith('.xml'):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    xml_files_found.append(file_path)
        
        if not xml_files_found:
            QMessageBox.information(self, "Info", f"Keine XML-Dateien im Ordner gefunden:\n{folder_path}")
            return
        
        # Dateien zur Liste hinzufügen
        added_count = 0
        for file_path in xml_files_found:
            # Prüfen ob schon in der Liste
            already_exists = any(xml_file['path'] == file_path for xml_file in self.xml_files)
            if not already_exists:
                xml_file = {
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size': os.path.getsize(file_path)
                }
                self.xml_files.append(xml_file)
                added_count += 1
        
        # Liste aktualisieren
        self.update_file_list()
        
        # Erste neue Datei auswählen
        if added_count > 0 and xml_files_found:
            self.select_file_in_list(xml_files_found[0])
        
        self.statusBar().showMessage(f"Ordner geladen: {added_count} neue XML-Dateien hinzugefügt")
    
    def update_file_list(self):
        """Dateiliste UI aktualisieren"""
        self.file_list.clear()
        
        for xml_file in self.xml_files:
            item = QListWidgetItem()
            
            # Text mit Dateiname und Größe
            size_kb = xml_file['size'] / 1024
            if size_kb > 1024:
                size_str = f"{size_kb/1024:.1f} MB"
            else:
                size_str = f"{size_kb:.1f} KB"
            
            item.setText(f"📄 {xml_file['name']}\n    {size_str}")
            item.setData(Qt.UserRole, xml_file['path'])
            
            self.file_list.addItem(item)
        
        # Info-Label aktualisieren
        count = len(self.xml_files)
        if count == 0:
            self.info_label.setText("Keine XML-Dateien geladen.\n\nVerwenden Sie das Datei-Menü zum Öffnen von:\n• XML-Dateien (Strg+O)\n• Ordnern (Strg+Shift+O)")
            self.info_label.show()
        elif count == 1:
            self.info_label.setText("1 XML-Datei geladen")
            self.info_label.hide()
        else:
            self.info_label.setText(f"{count} XML-Dateien geladen")
            self.info_label.hide()
    
    def select_file_in_list(self, file_path):
        """Datei in der Liste auswählen"""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.data(Qt.UserRole) == file_path:
                self.file_list.setCurrentItem(item)
                self.on_file_selected(item)
                break
    
    def on_file_selected(self, item):
        """Datei aus Liste ausgewählt"""
        file_path = item.data(Qt.UserRole)
        self.current_xml_file = file_path
        
        # HTML generieren und anzeigen
        self.generate_and_show_html(file_path)
        
        self.statusBar().showMessage(f"Angezeigt: {os.path.basename(file_path)}")
    
    def generate_and_show_html(self, xml_file_path):
        """HTML-Datei generieren und in WebView anzeigen"""
        try:
            # HTML generieren
            html_content = self.generate_html_from_xml(xml_file_path)
            
            # Temporäre HTML-Datei erstellen
            if self.temp_html_file:
                try:
                    os.unlink(self.temp_html_file)
                except:
                    pass
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                f.write(html_content)
                self.temp_html_file = f.name
            
            # In WebView laden
            file_url = QUrl.fromLocalFile(os.path.abspath(self.temp_html_file))
            self.webview.load(file_url)
            
        except Exception as e:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Fehler</title></head>
            <body style="font-family: Arial; padding: 40px; color: #721c24; background: #f8d7da;">
                <h2>❌ Fehler beim Laden der XML-Datei</h2>
                <p><strong>Datei:</strong> {xml_file_path}</p>
                <p><strong>Fehler:</strong> {str(e)}</p>
            </body>
            </html>
            """
            self.webview.setHtml(error_html)
    
    def generate_html_from_xml(self, xml_file_path):
        """HTML aus XML generieren - verwendet die bewährte Funktionalität aus squish_xml_html_gen.py"""
        
        # Die bewährten Funktionen aus squish_xml_html_gen.py importieren
        return self.generate_html_using_template(xml_file_path)
    
    def parse_object_xml(self, xml_path):
        """XML parsen (aus squish_xml_html_gen.py)"""
        try:
            # Read the file and skip non-XML content at the beginning
            with open(xml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the first XML tag
            xml_start = content.find('<ui')
            if xml_start == -1:
                xml_start = content.find('<')
            
            if xml_start > 0:
                content = content[xml_start:]
            
            # Parse the cleaned XML content
            root = ET.fromstring(content)
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return None
        return root

    def extract_image_from_element(self, element):
        """Extract base64 image from element if present (aus squish_xml_html_gen.py)"""
        image_elem = element.find('.//image[@type="PNG"]')
        if image_elem is not None and image_elem.text:
            return image_elem.text.strip()
        return None

    def build_tree_html(self, node, counter=None):
        """Tree HTML aufbauen (aus squish_xml_html_gen.py)"""
        if counter is None:
            counter = {"i": 1}
        myid = counter["i"]
        counter["i"] += 1

        # Build label from XML element, starting with simplifiedType if available
        simplified_type = node.attrib.get("simplifiedType", "")
        object_name = node.attrib.get("objectName", "")
        class_name = node.attrib.get("class", "")
        
        if simplified_type:
            if object_name:
                label = f"{simplified_type} ({object_name})"
            else:
                label = simplified_type
        else:
            # Fallback to original logic if no simplifiedType
            label = node.tag
            if object_name:
                label = f"{label} ({object_name})"
            elif class_name:
                label = f"{label} ({class_name})"
        
        # Collect all properties for this element
        properties = {}
        properties.update(node.attrib)  # Add XML attributes
        
        # Add realname if it exists
        realname_elem = node.find("realname")
        if realname_elem is not None and realname_elem.text:
            properties["realname"] = realname_elem.text.strip()
        
        # Add superclass information if it exists
        superclass_elem = node.find("superclass")
        if superclass_elem is not None:
            classes = [cls.text for cls in superclass_elem.findall("class") if cls.text]
            if classes:
                properties["superclasses"] = " > ".join(classes)
        
        # Add geometry information if it exists
        geom_elem = node.find("abstractProperties/geometry")
        if geom_elem is not None:
            for coord in ["x", "y", "width", "height"]:
                coord_elem = geom_elem.find(coord)
                if coord_elem is not None and coord_elem.text:
                    properties[f"geometry_{coord}"] = coord_elem.text
        
        # Add visual properties if they exist
        visual_elem = node.find("abstractProperties/visual")
        if visual_elem is not None:
            for attr_name, attr_value in visual_elem.attrib.items():
                properties[f"visual_{attr_name}"] = attr_value
        
        # Add properties from properties subelement if it exists
        props_elem = node.find("properties")
        if props_elem is not None:
            for prop in props_elem.findall("property"):
                prop_name = prop.attrib.get("name", "")
                prop_value = ""
                if prop.find("string") is not None:
                    prop_value = prop.find("string").text or ""
                properties[prop_name] = prop_value
        
        from html import escape
        data_props = escape(str(properties)).replace('"', '&quot;')
        xml_snippet = ET.tostring(node, encoding='unicode')
        data_xml = escape(xml_snippet).replace('"', '&quot;')
        
        html_parts = []
        html_parts.append(f'<li><span class="node" data-id="{myid}" data-props="{data_props}" data-xml="{data_xml}">{escape(label)}</span>')
        
        # Process children (look for 'children' element or direct child elements)
        children = []
        children_elem = node.find("children")
        if children_elem is not None:
            children = children_elem.findall("element")
        else:
            # Look for direct element children
            children = [child for child in node if child.tag == "element"]
        
        if children:
            html_parts.append("<ul>")
            for child in children:
                frag = self.build_tree_html(child, counter)[0]
                html_parts.append(frag)
            html_parts.append("</ul>")
        html_parts.append("</li>")
        return ("\n".join(html_parts), counter["i"])

    def generate_html_using_template(self, xml_file_path):
        """HTML generieren mit dem bewährten Template aus squish_xml_html_gen.py"""
        xml_root = self.parse_object_xml(xml_file_path)
        if xml_root is None:
            return "<html><body><h1>Fehler beim Parsen der XML-Datei</h1></body></html>"

        # Try to extract screenshot from first element with image
        screenshot_b64 = ""
        screenshot_name = ""
        
        # Look for image in the root or first element
        first_element = xml_root.find(".//element")
        if first_element is not None:
            image_data = self.extract_image_from_element(first_element)
            if image_data:
                screenshot_b64 = image_data
                screenshot_name = "Screenshot from XML"

        tree_html = "<p><i>No object structure found in XML.</i></p>"
        if xml_root is not None:
            # Try to build tree from the root or from elements
            if xml_root.find(".//element") is not None:
                # Find the root element to start from
                root_element = xml_root.find(".//element")
                tree_html_frag = self.build_tree_html(root_element)[0]
                tree_html = "<ul class='tree'>\n" + tree_html_frag + "\n</ul>"
            else:
                # Try to use the XML root directly
                tree_html_frag = self.build_tree_html(xml_root)[0]
                tree_html = "<ul class='tree'>\n" + tree_html_frag + "\n</ul>"

        # Get raw XML content
        with open(xml_file_path, "r", encoding="utf-8", errors="replace") as fh:
            raw_xml = fh.read()

        from html import escape
        title = escape(os.path.basename(xml_file_path))
        
        # Build the HTML string separately to avoid f-string issues with JavaScript
        screenshot_img = f"<img class='screenshot' src='data:image/png;base64,{screenshot_b64}'> " if screenshot_b64 else "<p><i>No screenshot found.</i></p>"
        
        # Das komplette Template aus squish_xml_html_gen.py
        html_template = '''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>XML Viewer - {TITLE}</title>
<style>
body{{font-family: Arial, Helvetica, sans-serif; margin:0; padding:0;}}
.header{{padding:10px; background:#2c3e50; color:white; display:flex; align-items:center; gap:15px;}}
.header h1{{margin:0; font-size:18px; color:white;}}
.header-search-group{{display:flex; align-items:center; gap:10px;}}
.header-search-group label{{font-size:12px; color:#ecf0f1; white-space:nowrap;}}
.header-search-group input, .header-search-group select{{padding:4px; border:none; border-radius:3px; font-size:12px;}}
.header-search-group .search-container{{position:relative;}}
.header .clear-btn{{color:#666; background:white;}}
.container{{display:flex; height:calc(100vh - 70px);}}
.sidebar{{width:360px; border-right:1px solid #ddd; display:flex; flex-direction:column;}}
.sidebar-header{{padding:10px; border-bottom:1px solid #eee; background:#f9f9f9;}}
.sidebar-content{{flex:1; padding:10px; overflow:auto;}}
.right-panel{{flex:1; display:flex; flex-direction:column;}}
.screenshot-panel{{height:320px; padding:10px; border-bottom:1px solid #ddd; overflow:hidden; flex-shrink:0;}}
.properties-panel{{flex:1; display:flex; flex-direction:column; min-height:0;}}
.properties-header{{padding:10px; border-bottom:1px solid #eee; background:#f9f9f9; flex-shrink:0;}}
.properties-content{{flex:1; padding:10px; overflow:auto; min-height:0;}}
.tree {{ list-style:none; padding-left:20px; }}
.tree li {{ margin:2px 0; }}
.node {{ cursor:pointer; display:inline-block; padding:2px 6px; border-radius:4px; }}
.node:hover {{ background:#eef; }}
.node.selected {{ background:#d0e7ff; }}
.props {{ white-space:pre-wrap; font-family: monospace; background:#f7f7f7; padding:8px; border-radius:4px; max-height:300px; overflow:auto; }}
.props-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
.props-table th, .props-table td {{ border:1px solid #ddd; padding:4px 8px; text-align:left; }}
.props-table th {{ background:#f0f0f0; font-weight:bold; }}
.props-table tr:nth-child(even) {{ background:#f9f9f9; }}
.props-table td:first-child {{ font-weight:bold; color:#666; max-width:150px; word-break:break-word; }}
.props-table td:last-child {{ font-family:monospace; max-width:200px; word-break:break-all; }}
.props-table .group-header {{ background:#e8f4fd; }}
.props-table .group-header td {{ font-weight:bold; color:#2c3e50; border-bottom:2px solid #3498db; }}
.props-table .group-item {{ background:#f8fcff; }}
.props-table .group-item td:first-child {{ padding-left:20px; font-style:italic; color:#34495e; }}
.props-table tr:hover {{ background:#f0f8ff; cursor:pointer; }}
.props-table tr.selected {{ background:#d4edda; }}
.props-table tr.selected td {{ background:transparent; }}
.context-menu {{ position:absolute; background:white; border:1px solid #ccc; border-radius:4px; padding:5px 0; box-shadow:2px 2px 10px rgba(0,0,0,0.3); z-index:1000; display:none; }}
.context-menu-item {{ padding:5px 15px; cursor:pointer; }}
.context-menu-item:hover {{ background:#f0f0f0; }}
.node {{ position:relative; }}
.props-table td {{ position:relative; }}
.search-container {{ position:relative; width:100%; }}
.search-container input {{ width:100%; box-sizing:border-box; }}
.clear-btn {{ position:absolute; right:5px; top:50%; transform:translateY(-50%); background:none; border:none; font-size:16px; cursor:pointer; color:#666; padding:0; width:20px; height:20px; display:none; }}
.clear-btn:hover {{ color:#333; background:#f0f0f0; border-radius:50%; }}
.search-container input:not(:placeholder-shown) + .clear-btn {{ display:block; }}
.screenshot {{ max-width:100%; max-height:280px; border:1px solid #ccc; object-fit:contain; }}
.screenshot-panel .panel {{ height:280px; overflow:auto; }}
.screenshot-container {{ position:relative; display:inline-block; max-width:100%; }}
.element-overlay {{ position:absolute; border:2px solid red; background:rgba(255,0,0,0.1); pointer-events:none; z-index:10; }}
.screenshot-panel {{ position:relative; }}
</style>
</head>
<body>
<div class="header">
  <h1>Object Viewer</h1>
  <div class="header-search-group">
    <label>Tree:</label>
    <div class="search-container">
      <input id="treeSearch" placeholder="Search tree..." style="width:150px; padding:4px; padding-right:25px;">
      <button id="clearTreeSearch" class="clear-btn" onclick="clearTreeSearch()" title="Clear search">&times;</button>
    </div>
  </div>
  <div class="header-search-group">
    <label>Properties:</label>
    <div class="search-container">
      <input id="propsSearch" placeholder="Search properties..." style="width:150px; padding:4px; padding-right:25px;">
      <button id="clearPropsSearch" class="clear-btn" onclick="clearPropsSearch()" title="Clear search">&times;</button>
    </div>
  </div>
  <div class="header-search-group">
    <label>Sort:</label>
    <select id="sortOrder" onchange="refreshProperties()" style="padding:4px;">
      <option value="desc">Descending</option>
      <option value="asc">Ascending</option>
      <option value="none">None</option>
    </select>
  </div>
</div>
<div class="container">
  <div class="sidebar">
    <div class="sidebar-header">
      <h3 style="margin:0;">Object Tree</h3>
    </div>
    <div class="sidebar-content">
      <div id="treeContainer">{TREE_HTML}</div>
    </div>
  </div>
  <div class="right-panel">
    <div class="screenshot-panel">
      <h3>Screenshot</h3>
      <div class="screenshot-container" id="screenshotContainer">
        {SCREENSHOT_IMG}
      </div>
      <p><small>{SCREENSHOT_NAME}</small></p>
    </div>
    <div class="properties-panel">
      <div class="properties-header">
        <h3 style="margin:0;">Selected Node Properties</h3>
      </div>
      <div class="properties-content">
        <div id="props">Click a node in the tree to see its properties here.</div>
      </div>
    </div>
  </div>
</div>

<!-- Context Menus -->
<div id="treeContextMenu" class="context-menu">
  <div class="context-menu-item" onclick="copyToClipboard('realname')">Copy realname</div>
  <div class="context-menu-item" onclick="copyToClipboard('class')">Copy class</div>
  <div class="context-menu-item" onclick="copyToClipboard('objectName')">Copy objectName</div>
</div>

<div id="propsContextMenu" class="context-menu">
  <div class="context-menu-item" onclick="copyToClipboard('propName')">Copy property name</div>
  <div class="context-menu-item" onclick="copyToClipboard('propValue')">Copy property value</div>
</div>

<script>
function formatPropertiesAsTable(propsStr, searchTerm) {
    try {
        // Decode HTML entities first
        var textarea = document.createElement('textarea');
        textarea.innerHTML = propsStr;
        var decodedStr = textarea.value;
        
        var props = eval("(" + decodedStr + ")");
        if (typeof props !== 'object' || props === null) {
            return "<p>No properties available</p>";
        }
        
        searchTerm = searchTerm || "";
        
        // Group properties hierarchically
        var groups = {};
        var standalone = {};
        
        for (var key in props) {
            if (props.hasOwnProperty(key)) {
                var parts = key.split('_');
                if (parts.length > 1) {
                    var groupName = parts[0];
                    var propName = parts.slice(1).join('_');
                    if (!groups[groupName]) groups[groupName] = {};
                    groups[groupName][propName] = props[key];
                } else if (key === 'superclasses') {
                    // Split superclasses into individual items
                    if (!groups['superclasses']) groups['superclasses'] = {};
                    var classes = props[key].split(' > ');
                    for (var i = 0; i < classes.length; i++) {
                        groups['superclasses']['level_' + i] = classes[i];
                    }
                } else {
                    standalone[key] = props[key];
                }
            }
        }
        
        // Get sort order from dropdown (default: descending)
        var sortOrder = document.getElementById('sortOrder') ? document.getElementById('sortOrder').value : 'desc';
        
        // Sort function
        function sortKeys(obj) {
            var keys = Object.keys(obj);
            if (sortOrder === 'asc') {
                keys.sort();
            } else if (sortOrder === 'desc') {
                keys.sort().reverse();
            }
            // 'none' = no sorting, keep original order
            return keys;
        }
        
        var table = "<table class='props-table'>";
        table += "<thead><tr><th>Property</th><th>Value</th></tr></thead><tbody>";
        
        // Filter and add standalone properties first (sorted)
        var standaloneKeys = sortKeys(standalone);
        for (var i = 0; i < standaloneKeys.length; i++) {
            var key = standaloneKeys[i];
            var value = standalone[key];
            if (value === null || value === undefined) value = "";
            
            // Apply search filter
            if (searchTerm === "" || 
                key.toLowerCase().includes(searchTerm) || 
                value.toString().toLowerCase().includes(searchTerm)) {
                table += "<tr><td>" + key + "</td><td>" + value + "</td></tr>";
            }
        }
        
        // Filter and add grouped properties with hierarchy (sorted groups)
        var groupKeys = sortKeys(groups);
        for (var i = 0; i < groupKeys.length; i++) {
            var groupName = groupKeys[i];
            var groupHasMatches = false;
            var groupContent = "";
            
            // Sort properties within each group and check for matches
            var groupPropKeys = sortKeys(groups[groupName]);
            for (var j = 0; j < groupPropKeys.length; j++) {
                var propName = groupPropKeys[j];
                var value = groups[groupName][propName];
                if (value === null || value === undefined) value = "";
                var displayName = propName.replace('level_', 'inheritance_');
                
                // Apply search filter
                if (searchTerm === "" || 
                    groupName.toLowerCase().includes(searchTerm) ||
                    displayName.toLowerCase().includes(searchTerm) || 
                    value.toString().toLowerCase().includes(searchTerm)) {
                    groupContent += "<tr class='group-item'><td>&nbsp;&nbsp;&nbsp;&nbsp;" + displayName + "</td><td>" + value + "</td></tr>";
                    groupHasMatches = true;
                }
            }
            
            // Only add group if it has matches
            if (groupHasMatches) {
                table += "<tr class='group-header'><td colspan='2'><strong>" + groupName + "</strong></td></tr>";
                table += groupContent;
            }
        }
        
        table += "</tbody></table>";
        
        // Add click handlers to table rows after table is created
        setTimeout(function() {
            var tableRows = document.querySelectorAll('.props-table tr:not(.group-header)');
            tableRows.forEach(function(row) {
                row.addEventListener('click', function() {
                    // Remove selection from all rows
                    document.querySelectorAll('.props-table tr').forEach(function(r) {
                        r.classList.remove('selected');
                    });
                    // Add selection to clicked row
                    this.classList.add('selected');
                });
            });
        }, 10);
        
        return table;
    } catch(e) {
        return "<p class='props'>" + propsStr + "</p>";
    }
}

var currentSelectedNode = null;

var originalTreeHTML = "";
var currentPropsData = null;
var currentContextNode = null;
var currentContextPropName = null;
var currentContextPropValue = null;
var screenshotGeometry = null;

function refreshProperties() {
    if (currentSelectedNode) {
        var props = currentSelectedNode.getAttribute("data-props") || "{{}}";
        currentPropsData = props;
        filterAndDisplayProperties();
        updateElementOverlay();
    }
}

function updateElementOverlay() {
    // Remove existing overlay
    var existingOverlay = document.getElementById('elementOverlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    if (!currentSelectedNode) return; 
    
    var props = currentSelectedNode.getAttribute("data-props") || "{{}}";
    try {
        var textarea = document.createElement('textarea');
        textarea.innerHTML = props;
        var decodedStr = textarea.value;
        var propsObj = eval("(" + decodedStr + ")");
        
        // Check if element has geometry properties
        var elemX = propsObj['geometry_x'];
        var elemY = propsObj['geometry_y'];
        var elemWidth = propsObj['geometry_width'];
        var elemHeight = propsObj['geometry_height'];
        
        if (elemX !== undefined && elemY !== undefined && elemWidth !== undefined && elemHeight !== undefined) {
            // Get screenshot geometry (assume first element or root has the screenshot dimensions)
            if (!screenshotGeometry) {
                // Try to find screenshot geometry from the first element with geometry
                var allNodes = document.querySelectorAll('.node');
                for (var i = 0; i < allNodes.length; i++) {
                    var nodeProps = allNodes[i].getAttribute("data-props") || "{{}}";
                    try {
                        var nodeTextarea = document.createElement('textarea');
                        nodeTextarea.innerHTML = nodeProps;
                        var nodeDecoded = nodeTextarea.value;
                        var nodePropsObj = eval("(" + nodeDecoded + ")");
                        if (nodePropsObj['geometry_x'] !== undefined) {
                            screenshotGeometry = {
                                x: parseInt(nodePropsObj['geometry_x']) || 0,
                                y: parseInt(nodePropsObj['geometry_y']) || 0
                            };
                            break;
                        }
                    } catch(e) {}
                }
                if (!screenshotGeometry) {
                    screenshotGeometry = {x: 0, y: 0}; // Default fallback
                }
            }
            
            drawElementOverlay(
                parseInt(elemX) - screenshotGeometry.x,
                parseInt(elemY) - screenshotGeometry.y,
                parseInt(elemWidth),
                parseInt(elemHeight)
            );
        }
    } catch(e) {
        console.log('Error parsing properties for overlay:', e);
    }
}

function drawElementOverlay(x, y, width, height) {
    var screenshotImg = document.querySelector('.screenshot');
    var container = document.getElementById('screenshotContainer');
    
    if (!screenshotImg || !container) return;
    
    // Screenshot is always visible now
    
    // Get actual displayed image dimensions
    var imgRect = screenshotImg.getBoundingClientRect();
    var containerRect = container.getBoundingClientRect();
    
    // Calculate scale factor between actual image and displayed image
    var scaleX = imgRect.width / screenshotImg.naturalWidth;
    var scaleY = imgRect.height / screenshotImg.naturalHeight;
    
    // Calculate overlay position and size
    var overlayX = x * scaleX;
    var overlayY = y * scaleY;
    var overlayWidth = width * scaleX;
    var overlayHeight = height * scaleY;
    
    // Create overlay element
    var overlay = document.createElement('div');
    overlay.id = 'elementOverlay';
    overlay.className = 'element-overlay';
    overlay.style.left = overlayX + 'px';
    overlay.style.top = overlayY + 'px';
    overlay.style.width = overlayWidth + 'px';
    overlay.style.height = overlayHeight + 'px';
    
    container.appendChild(overlay);
}

function filterAndDisplayProperties() {
    if (!currentPropsData) return;
    
    var searchTerm = document.getElementById('propsSearch').value.toLowerCase();
    var html = formatPropertiesAsTable(currentPropsData, searchTerm);
    document.getElementById("props").innerHTML = html;
}

function filterTree() {
    var searchTerm = document.getElementById('treeSearch').value.toLowerCase();
    var treeContainer = document.getElementById('treeContainer');
    
    if (searchTerm === '') {
        // Show all nodes
        var allNodes = treeContainer.querySelectorAll('li');
        allNodes.forEach(function(node) {
            node.style.display = '';
        });
        var allUls = treeContainer.querySelectorAll('ul');
        allUls.forEach(function(ul) {
            ul.style.display = '';
        });
    } else {
        // Hide all nodes first
        var allNodes = treeContainer.querySelectorAll('li');
        allNodes.forEach(function(node) {
            node.style.display = 'none';
        });
        
        // Show matching nodes and their parents
        var nodeSpans = treeContainer.querySelectorAll('.node');
        nodeSpans.forEach(function(span) {
            if (span.textContent.toLowerCase().includes(searchTerm)) {
                // Show this node and all its parents
                var current = span.closest('li');
                while (current) {
                    current.style.display = '';
                    // Show parent ul and li
                    var parentUl = current.parentElement;
                    if (parentUl && parentUl.tagName === 'UL') {
                        parentUl.style.display = '';
                        var parentLi = parentUl.parentElement;
                        if (parentLi && parentLi.tagName === 'LI') {
                            parentLi.style.display = '';
                            current = parentLi;
                        } else {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
        });
    }
}

document.addEventListener("click", function(e){
    if(e.target.classList.contains("node")){
        document.querySelectorAll(".node").forEach(n=>n.classList.remove("selected"));
        e.target.classList.add("selected");
        currentSelectedNode = e.target;
        var props = e.target.getAttribute("data-props") || "{{}}";
        currentPropsData = props;
        filterAndDisplayProperties();
        updateElementOverlay();
    }

});

// Add context menu event listeners after DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
    // Tree context menu
    document.addEventListener('contextmenu', function(e) {
        if (e.target.classList.contains('node')) {
            showTreeContextMenu(e, e.target);
        }
    });
    
    // Properties table context menu  
    document.addEventListener('contextmenu', function(e) {
        var targetCell = e.target.closest('.props-table td');
        if (targetCell) {
            var row = targetCell.parentElement;
            // Ensure it's a property row, not a group header
            if (row.cells.length === 2) {
                var propName = row.cells[0].textContent.trim();
                var propValue = row.cells[1].textContent.trim();
                showPropsContextMenu(e, propName, propValue);
            }
        }
    });
});

// Add search functionality
document.getElementById("treeSearch").addEventListener("input", function() {
    filterTree();
    toggleClearButton('treeSearch', 'clearTreeSearch');
});
document.getElementById("propsSearch").addEventListener("input", function() {
    filterAndDisplayProperties();
    toggleClearButton('propsSearch', 'clearPropsSearch');
});

function toggleClearButton(inputId, buttonId) {
    var input = document.getElementById(inputId);
    var button = document.getElementById(buttonId);
    if (input.value.length > 0) {
        button.style.display = 'block';
    } else {
        button.style.display = 'none';
    }
}

function clearTreeSearch() {
    var input = document.getElementById('treeSearch');
    input.value = '';
    input.focus();
    filterTree();
    toggleClearButton('treeSearch', 'clearTreeSearch');
}

function clearPropsSearch() {
    var input = document.getElementById('propsSearch');
    input.value = '';
    input.focus();
    filterAndDisplayProperties();
    toggleClearButton('propsSearch', 'clearPropsSearch');
}

// Initialize original tree HTML and context menus
document.addEventListener("DOMContentLoaded", function() {
    originalTreeHTML = document.getElementById('treeContainer').innerHTML;
});

// Update overlay when window is resized
window.addEventListener('resize', function() {
    setTimeout(updateElementOverlay, 100);
});

// Context menu functions
function copyToClipboard(type) {
    var textToCopy = "";
    var what = "";

    if (type === 'realname' || type === 'class' || type === 'objectName') {
        what = type;
        if (currentContextNode) {
            var props = currentContextNode.getAttribute("data-props") || "{{}}";
            try {
                var textarea = document.createElement('textarea');
                textarea.innerHTML = props;
                var decodedStr = textarea.value;
                var propsObj = eval("(" + decodedStr + ")");
                textToCopy = propsObj[type] || "";
            } catch(e) {
                textToCopy = "Property not found";
            }
        }
    } else if (type === 'propName') {
        what = "Property name";
        textToCopy = currentContextPropName || "";
    } else if (type === 'propValue') {
        what = "Property value";
        textToCopy = currentContextPropValue || "";
    }

    function showToast(message) {
        var feedback = document.createElement('div');
        feedback.textContent = message;
        feedback.style.cssText = 'position:fixed;top:20px;right:20px;background:#2c3e50;color:white;padding:10px 20px;border-radius:4px;z-index:10000;font-family:Arial,sans-serif;font-size:14px;';
        document.body.appendChild(feedback);
        setTimeout(function() { document.body.removeChild(feedback); }, 2500);
    }

    if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(function() {
            var shortText = textToCopy.length > 50 ? textToCopy.substring(0, 47) + '...' : textToCopy;
            showToast('Copied "' + shortText + '" to clipboard.');
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            // Fallback for older browsers
            var textArea = document.createElement('textarea');
            textArea.value = textToCopy;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                var shortText = textToCopy.length > 50 ? textToCopy.substring(0, 47) + '...' : textToCopy;
                showToast('Copied "' + shortText + '" to clipboard.');
            } catch (copyErr) {
                showToast('Failed to copy.');
            }
            document.body.removeChild(textArea);
        });
    }
    
    hideContextMenus();
}

function hideContextMenus() {
    document.getElementById('treeContextMenu').style.display = 'none';
    document.getElementById('propsContextMenu').style.display = 'none';
}

function showTreeContextMenu(e, node) {
    e.preventDefault();
    currentContextNode = node;
    var menu = document.getElementById('treeContextMenu');
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
}

function showPropsContextMenu(e, propName, propValue) {
    e.preventDefault();
    currentContextPropName = propName;
    currentContextPropValue = propValue;
    var menu = document.getElementById('propsContextMenu');
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
}

function getSelectedNodeXml() {
    if (currentSelectedNode) {
        var xml_string = currentSelectedNode.getAttribute("data-xml");
        if (xml_string) {
            // Decode HTML entities
            var textarea = document.createElement('textarea');
            textarea.innerHTML = xml_string;
            return textarea.value;
        }
    }
    return null;
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Hide context menus when clicking elsewhere
document.addEventListener('click', hideContextMenus);
document.addEventListener('contextmenu', function(e) {
    if (!e.target.closest('.context-menu')) {
        hideContextMenus();
    }
});
</script>

<!-- Hidden XML data for copying -->
<div id="rawXmlData" style="display:none;">{RAW_XML}</div>

</body>
</html>
'''
        
        # Template befüllen
        html = html_template.replace('{{', '{').replace('}}', '}')
        
        # Replace placeholders with actual values using simple string replacement
        html = html.replace('{TITLE}', title)
        html = html.replace('{TREE_HTML}', tree_html)
        html = html.replace('{SCREENSHOT_IMG}', screenshot_img)
        html = html.replace('{SCREENSHOT_NAME}', escape(screenshot_name))
        html = html.replace('{RAW_XML}', escape(raw_xml))
        
        return html
    
    def xml_to_js_data(self, xml_element):
        """XML-Element zu JavaScript-Daten konvertieren"""
        data = {
            'tag': xml_element.tag,
            'attributes': xml_element.attrib,
            'properties': [],
            'geometry': {},
            'children': []
        }
        
        # Properties extrahieren
        props_elem = xml_element.find('properties')
        if props_elem is not None:
            for prop in props_elem.findall('property'):
                prop_name = prop.get('name', '')
                prop_value = prop.text
                if prop_value is None:
                    string_elem = prop.find('string')
                    if string_elem is not None:
                        prop_value = string_elem.text or ""
                data['properties'].append({
                    'name': prop_name,
                    'value': prop_value or ""
                })
        
        # Geometrie extrahieren
        geometry_elem = xml_element.find('.//geometry')
        if geometry_elem is not None:
            for child in geometry_elem:
                if child.text:
                    try:
                        data['geometry'][child.tag] = float(child.text)
                    except ValueError:
                        data['geometry'][child.tag] = child.text
        
        # Kinder
        for child in xml_element:
            if child.tag == 'element':
                data['children'].append(self.xml_to_js_data(child))
            elif child.tag == 'children':
                for grandchild in child:
                    if grandchild.tag == 'element':
                        data['children'].append(self.xml_to_js_data(grandchild))
        
        return data
    
    def generate_tree_html(self, xml_element, level=0):
        """Tree HTML generieren"""
        html = ""
        
        def process_element(elem, lvl):
            nonlocal html
            
            # Display-Text bestimmen
            display_text = elem.tag
            if elem.tag == 'element':
                simplified_type = elem.get('simplifiedType', '')
                class_name = elem.get('class', '')
                
                if simplified_type:
                    display_text = simplified_type
                    if class_name:
                        display_text += f" [{class_name}]"
                elif class_name:
                    display_text = class_name
            
            # Tree-Item
            has_children = any(child.tag in ['element', 'children'] for child in elem)
            expandable_class = 'expandable' if has_children else ''
            
            element_data = self.xml_to_js_data(elem)
            onclick = f"selectElement({json.dumps(element_data, ensure_ascii=False)})"
            
            if has_children:
                onclick += f"; toggleTreeItem(event)"
            
            html += f'<div class="tree-item {expandable_class}" onclick="{onclick}">{display_text}</div>'
            
            # Kinder
            if has_children:
                html += '<div class="tree-children">'
                for child in elem:
                    if child.tag == 'element':
                        process_element(child, lvl + 1)
                    elif child.tag == 'children':
                        for grandchild in child:
                            if grandchild.tag == 'element':
                                process_element(grandchild, lvl + 1)
                html += '</div>'
        
        process_element(xml_element, level)
        return html
    
    def generate_screenshot_html(self, xml_element):
        """Screenshot HTML generieren"""
        # Suche nach <image> Element
        for elem in xml_element.iter():
            if elem.tag == 'image' and elem.get('type') == 'PNG':
                try:
                    # Base64-Image direkt einbetten
                    image_data = elem.text
                    return f'<img id="screenshot" src="data:image/png;base64,{image_data}" alt="Screenshot" />'
                except Exception as e:
                    return f'<div style="padding: 40px; text-align: center; color: #666;">Fehler beim Laden des Screenshots: {e}</div>'
        
        return '<div style="padding: 40px; text-align: center; color: #666;">Kein Screenshot verfügbar</div>'
    
    def clear_file_list(self):
        """Dateiliste leeren"""
        self.xml_files = []
        self.current_xml_file = None
        self.update_file_list()
        self.load_welcome_page()
        self.statusBar().showMessage("Dateiliste geleert")
    
    def reload_webview(self):
        """WebView neu laden"""
        if self.current_xml_file:
            self.generate_and_show_html(self.current_xml_file)
        else:
            self.webview.reload()
        self.statusBar().showMessage("WebView neu geladen")
    
    def open_in_browser(self):
        """Aktuelle HTML-Datei im externen Browser öffnen"""
        if self.temp_html_file and os.path.exists(self.temp_html_file):
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(self.temp_html_file)}")
            self.statusBar().showMessage("HTML-Datei im Browser geöffnet")
        else:
            QMessageBox.information(self, "Info", "Keine HTML-Datei zum Öffnen verfügbar")
    
    def show_about(self):
        """Über-Dialog anzeigen"""
        about_text = """
        <h3>Squish XML Hybrid Viewer</h3>
        
        <p>Eine hybride Desktop-Anwendung zur Anzeige von Squish XML-Dateien.</p>
        
        <p><b>Features:</b></p>
        <ul>
        <li>Dreipanel-Layout mit Tree, Screenshot und Properties</li>
        <li>Such- und Filterfunktionen</li>
        <li>Screenshot-Overlays für UI-Elemente</li>
        <li>Kontextmenüs mit Clipboard-Integration</li>
        <li>HTML-Export und Browser-Ansicht</li>
        </ul>
        
        <p><b>Tastenkürzel:</b></p>
        <ul>
        <li><b>Strg+O:</b> XML-Datei öffnen</li>
        <li><b>Strg+Shift+O:</b> Ordner öffnen</li>
        <li><b>Strg+L:</b> Liste leeren</li>
        <li><b>F5:</b> WebView neu laden</li>
        <li><b>Strg+B:</b> In Browser öffnen</li>
        <li><b>Strg+Q:</b> Beenden</li>
        </ul>
        
        <p><small>Powered by PyQt5 + QWebEngineView</small></p>
        """
        
        QMessageBox.about(self, "Über Squish XML Viewer", about_text)

    def closeEvent(self, event):
        """Anwendung schließen - Aufräumen"""
        if self.temp_html_file:
            try:
                os.unlink(self.temp_html_file)
            except:
                pass
        event.accept()


def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # App-Styling (ohne Menü-Styling für native macOS-Menüs)
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f6f8fa;
        }
    """)
    
    viewer = SquishXMLHybridViewer()
    viewer.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()