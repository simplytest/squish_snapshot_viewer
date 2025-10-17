#!/usr/bin/env python3
"""
squish_xml_viewer_desktop.py

Desktop-App für Squish XML Viewer - Nachbildung der HTML-Version mit PyQt5
Exakt gleiche Funktionalität wie in squishsnapshot_viewer.html

Features:
- Header mit Tree/Properties-Suche und Sort-Optionen
- Drei-Panel Layout: Links Tree, rechts oben Screenshot, rechts unten Properties  
- Element-Overlays auf Screenshots
- Kontextmenüs mit Kopieren-Funktionen
- Deutsche Toast-Benachrichtigungen
- Genau wie die HTML-Version
"""

import sys
import os
import xml.etree.ElementTree as ET
import base64
from io import BytesIO

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
        QSplitter, QMenu, QAction, QFileDialog, QMessageBox, QLineEdit,
        QLabel, QPushButton, QStatusBar, QFrame, QComboBox, QGroupBox,
        QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
        QGraphicsRectItem, QTextEdit, QHeaderView
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QPixmap, QImage, QPen, QBrush, QColor, QFont, QPainter
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class ToastNotification(QWidget):
    """Toast-Benachrichtigungen wie in der HTML-Version"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QHBoxLayout(self)
        self.label = QLabel()
        self.label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.label)
        
        # Timer für automatisches Ausblenden
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide)
    
    def show_toast(self, message, toast_type="success", duration=3000):
        """Toast anzeigen"""
        self.label.setText(message)
        
        # Farbe je nach Typ
        if toast_type == "success":
            bg_color = "#4CAF50"  # Grün
        else:
            bg_color = "#f44336"  # Rot
            
        self.label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                padding: 10px 15px;
                border-radius: 4px;
                font-weight: bold;
            }}
        """)
        
        # Position rechts oben
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.right() - self.sizeHint().width() - 20, 50)
        
        self.show()
        self.timer.start(duration)


class SquishXMLDesktopViewer(QMainWindow):
    """Hauptklasse - exakte Nachbildung der HTML-Version"""
    
    def __init__(self):
        super().__init__()
        
        if not PYQT_AVAILABLE:
            print("❌ PyQt5 nicht verfügbar! Installieren Sie: pip install PyQt5")
            sys.exit(1)
        
        self.current_file = None
        self.xml_data = None
        self.image_scale_factor = 1.0
        self.original_elements = []  # Für Suche
        
        # Toast-System
        self.toast = ToastNotification(self)
        
        self.init_ui()
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
    
    def init_ui(self):
        """UI erstellen - Verbessertes Layout ohne Menü"""
        self.setWindowTitle("Object Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Header (verbessertes Design)
        self.create_header(main_layout)
        
        # Container mit Sidebar links, rechts zwei Panels übereinander
        container = QSplitter(Qt.Horizontal)
        main_layout.addWidget(container)
        
        # Links: Sidebar (Object Tree)
        self.create_sidebar(container)
        
        # Rechts: Screenshot oben, Properties unten
        right_splitter = QSplitter(Qt.Vertical)
        container.addWidget(right_splitter)
        
        self.create_screenshot_panel(right_splitter)
        self.create_properties_panel(right_splitter)
        
        # Splitter-Verhältnisse setzen
        container.setSizes([360, 1040])  # Wie in HTML: 360px sidebar
        right_splitter.setSizes([320, 580])  # Screenshot 320px, Properties Rest
        
        # Einfaches Menü hinzufügen
        self.create_simple_menu()
    
    def create_header(self, parent_layout):
        """Kompakter Header mit besserer Höhe"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e1e4e8;
                padding: 12px 20px;
            }
        """)
        header.setFixedHeight(55)
        parent_layout.addWidget(header)
        
        layout = QHBoxLayout(header)
        layout.setSpacing(30)
        
        # Title und Button
        left_layout = QHBoxLayout()
        
        title = QLabel("Object Viewer")
        title.setStyleSheet("""
            font-size: 18px; 
            font-weight: 600; 
            color: #24292e;
            margin: 0;
        """)
        left_layout.addWidget(title)
        
        # Datei öffnen Button mit Menü
        self.open_btn = QPushButton("📁 Datei öffnen")
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #0366d6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                margin-left: 15px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #0256cc;
            }
        """)
        self.open_btn.clicked.connect(self.open_file_dialog)
        left_layout.addWidget(self.open_btn)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Such-Controls - horizontal, sauber
        search_layout = QHBoxLayout()
        search_layout.setSpacing(20)
        
        # Tree Search
        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("Tree durchsuchen...")
        self.tree_search.setFixedWidth(180)
        self.tree_search.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                font-size: 14px;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                background-color: #fafbfc;
                min-height: 30px;
            }
            QLineEdit:focus {
                border-color: #0366d6;
                background-color: white;
            }
        """)
        self.tree_search.textChanged.connect(self.filter_tree)
        search_layout.addWidget(self.tree_search)
        
        # Properties Search
        self.props_search = QLineEdit()
        self.props_search.setPlaceholderText("Properties durchsuchen...")
        self.props_search.setFixedWidth(180)
        self.props_search.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                font-size: 14px;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                background-color: #fafbfc;
                min-height: 30px;
            }
            QLineEdit:focus {
                border-color: #0366d6;
                background-color: white;
            }
        """)
        self.props_search.textChanged.connect(self.filter_properties)
        search_layout.addWidget(self.props_search)
        
        # Sort Dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Sortierung", "A→Z", "Z→A"])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                padding: 10px 12px;
                font-size: 14px;
                border: 1px solid #d1d5da;
                border-radius: 6px;
                background-color: #fafbfc;
                min-width: 120px;
                min-height: 30px;
            }
            QComboBox:hover {
                border-color: #0366d6;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.sort_combo.currentTextChanged.connect(self.refresh_properties)
        search_layout.addWidget(self.sort_combo)
        
        layout.addLayout(search_layout)
    
    def create_simple_menu(self):
        """Einfaches Menü für Dateifunktionen"""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu('Datei')
        
        open_action = file_menu.addAction('XML-Datei öffnen...')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file_dialog)
        
        file_menu.addSeparator()
        
        reload_action = file_menu.addAction('Neu laden')
        reload_action.setShortcut('Ctrl+R') 
        reload_action.triggered.connect(self.reload_file)
        
        close_action = file_menu.addAction('Datei schließen')
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close_file)

    def create_sidebar(self, parent_splitter):
        """Saubere Sidebar mit Object Tree"""
        sidebar = QFrame()
        sidebar.setFrameStyle(QFrame.NoFrame)
        sidebar.setFixedWidth(360)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #f6f8fa;
                border-right: 1px solid #e1e4e8;
            }
        """)
        parent_splitter.addWidget(sidebar)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #f6f8fa;
                padding: 16px;
                border-bottom: 1px solid #e1e4e8;
            }
        """)
        layout.addWidget(header)
        
        header_layout = QVBoxLayout(header)
        title = QLabel("Object Tree")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600; 
            color: #24292e;
            margin: 0;
        """)
        header_layout.addWidget(title)
        
        # Tree Widget - clean
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: #f6f8fa;
                font-size: 14px;
                padding: 0;
                outline: none;
            }
            QTreeWidget::item {
                height: 32px;
                padding: 6px 16px;
                color: #24292e;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #0366d6;
                color: white;
            }
            QTreeWidget::item:hover:!selected {
                background-color: #f1f8ff;
            }
            QTreeWidget::branch:has-children:closed {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOCIgaGVpZ2h0PSI4IiBmaWxsPSIjNTg2MDY5IiB2aWV3Qm94PSIwIDAgMTYgMTYiPjxwYXRoIGQ9Ik02IDEyTDEwIDhMNiA0djh6Ii8+PC9zdmc+);
            }
            QTreeWidget::branch:has-children:open {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOCIgaGVpZ2h0PSI4IiBmaWxsPSIjNTg2MDY5IiB2aWV3Qm94PSIwIDAgMTYgMTYiPjxwYXRoIGQ9Ik0xMiA2TDggMTBMNCA2aDh6Ii8+PC9zdmc+);
            }
        """)
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)
        layout.addWidget(self.tree_widget)
        
        # Kontextmenü für Tree
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
    
    def create_screenshot_panel(self, parent_splitter):
        """Screenshot Panel - clean design"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.NoFrame)
        panel.setMinimumHeight(320)
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e1e4e8;
            }
        """)
        parent_splitter.addWidget(panel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame() 
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                padding: 16px;
                border-bottom: 1px solid #e1e4e8;
            }
        """)
        layout.addWidget(header)
        
        header_layout = QVBoxLayout(header)
        title = QLabel("Screenshot")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600; 
            color: #24292e;
            margin: 0;
        """)
        header_layout.addWidget(title)
        
        # Graphics View für Screenshot mit Overlays
        self.screenshot_view = QGraphicsView()
        self.screenshot_scene = QGraphicsScene()
        self.screenshot_view.setScene(self.screenshot_scene)
        self.screenshot_view.setStyleSheet("""
            QGraphicsView {
                border: none;
                background-color: #fafbfc;
            }
        """)
        layout.addWidget(self.screenshot_view)
    
    def create_properties_panel(self, parent_splitter):
        """Properties Panel - clean design"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.NoFrame)
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
            }
        """)
        parent_splitter.addWidget(panel)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                padding: 16px;
                border-bottom: 1px solid #e1e4e8;
            }
        """)
        layout.addWidget(header)
        
        header_layout = QVBoxLayout(header)
        title = QLabel("Properties")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600; 
            color: #24292e;
            margin: 0;
        """)
        header_layout.addWidget(title)
        
        # Properties Table - clean und gut lesbar
        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(2)
        self.properties_table.setHorizontalHeaderLabels(["Property", "Value"])
        
        # Spaltenbreiten optimieren
        self.properties_table.horizontalHeader().setStretchLastSection(True)
        self.properties_table.setColumnWidth(0, 200)
        
        # Zeilennummern sichtbar und gut lesbar machen
        self.properties_table.verticalHeader().setVisible(True)
        self.properties_table.verticalHeader().setDefaultSectionSize(30)
        
        self.properties_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
                font-size: 14px;
                gridline-color: #e1e4e8;
                outline: none;
                selection-background-color: #0366d6;
            }
            QTableWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #e1e4e8;
                color: #24292e;
                min-height: 20px;
            }
            QTableWidget::item:selected {
                background-color: #0366d6;
                color: white;
            }
            QTableWidget::item:hover:!selected {
                background-color: #f1f8ff;
            }
            QHeaderView::section {
                background-color: #f6f8fa;
                font-size: 14px;
                font-weight: 600;
                color: #24292e;
                border: none;
                border-right: 1px solid #e1e4e8;
                border-bottom: 1px solid #e1e4e8;
                padding: 10px 12px;
            }
            QHeaderView::section:vertical {
                background-color: #f6f8fa;
                font-size: 12px;
                font-weight: normal;
                color: #586069;
                border: none;
                border-right: 1px solid #e1e4e8;
                border-bottom: 1px solid #e1e4e8;
                padding: 4px 8px;
                min-width: 40px;
            }
        """)
        layout.addWidget(self.properties_table)
        
        # Kontextmenü für Properties
        self.properties_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.properties_table.customContextMenuRequested.connect(self.show_properties_context_menu)
    

    
    def open_file_dialog(self):
        """Datei-Öffnen Dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "XML-Datei öffnen", "", "XML Files (*.xml);;All Files (*)"
        )
        if file_path:
            self.load_xml_file(file_path)
    
    def load_xml_file(self, file_path):
        """XML-Datei laden und anzeigen"""
        try:
            self.current_file = file_path
            
            # XML parsen
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            
            # UI aktualisieren
            self.setWindowTitle(f"Object Viewer - {os.path.basename(file_path)}")
            
            # Tree aufbauen
            self.populate_tree()
            
            # Screenshot laden
            self.load_screenshot()
            
            # Properties leeren
            self.properties_table.setRowCount(0)
            
            self.toast.show_toast(f"XML-Datei '{os.path.basename(file_path)}' geladen", "success")
            self.statusBar().showMessage(f"Geladen: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der XML-Datei:\n{str(e)}")
    
    def populate_tree(self):
        """Tree mit XML-Daten füllen (wie HTML-Version)"""
        self.tree_widget.clear()
        self.original_elements = []  # Für Suche zurücksetzen
        
        if self.xml_data is not None:
            self.add_tree_item(None, self.xml_data)
            
            # Ersten Knoten expandieren
            if self.tree_widget.topLevelItemCount() > 0:
                self.tree_widget.topLevelItem(0).setExpanded(True)
    
    def add_tree_item(self, parent_item, xml_element):
        """Tree-Item hinzufügen (rekursiv)"""
        # Display-Text bestimmen
        display_text = xml_element.tag
        
        if xml_element.tag == 'element':
            # Für <element> verwende class und simplifiedType wie in HTML
            class_name = xml_element.get('class', '')
            simplified_type = xml_element.get('simplifiedType', '')
            
            if simplified_type:
                display_text = f"{simplified_type}"
                if class_name:
                    display_text += f" [{class_name}]"
            elif class_name:
                display_text = class_name
        
        # Tree-Item erstellen
        if parent_item is None:
            tree_item = QTreeWidgetItem(self.tree_widget)
        else:
            tree_item = QTreeWidgetItem(parent_item)
        
        tree_item.setText(0, display_text)
        tree_item.setData(0, Qt.UserRole, xml_element)  # XML-Element speichern
        
        # Für Suche speichern
        self.original_elements.append((tree_item, xml_element))
        
        # Kinder hinzufügen (nur relevante)
        for child in xml_element:
            if child.tag in ['element', 'children']:
                if child.tag == 'children':
                    # Für <children> die enthaltenen <element> direkt hinzufügen
                    for grandchild in child:
                        if grandchild.tag == 'element':
                            self.add_tree_item(tree_item, grandchild)
                else:
                    self.add_tree_item(tree_item, child)
    
    def load_screenshot(self):
        """Screenshot laden und anzeigen"""
        self.screenshot_scene.clear()
        
        try:
            # Suche nach <image> Element
            for elem in self.xml_data.iter():
                if elem.tag == 'image' and elem.get('type') == 'PNG':
                    try:
                        # Base64 dekodieren
                        image_data = base64.b64decode(elem.text)
                        
                        # QImage erstellen
                        qimage = QImage()
                        qimage.loadFromData(image_data, 'PNG')
                        
                        if not qimage.isNull():
                            # Skalieren für Anzeige
                            max_width, max_height = 580, 280
                            if qimage.width() > max_width or qimage.height() > max_height:
                                qimage = qimage.scaled(max_width, max_height, 
                                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
                                self.image_scale_factor = min(max_width / qimage.width(), 
                                                            max_height / qimage.height())
                            else:
                                self.image_scale_factor = 1.0
                            
                            # QPixmap erstellen und anzeigen
                            pixmap = QPixmap.fromImage(qimage)
                            self.screenshot_scene.addPixmap(pixmap)
                            
                            # Element-Overlays hinzufügen
                            self.add_element_overlays()
                            
                            return
                    
                    except Exception as e:
                        print(f"Fehler beim Dekodieren des Screenshots: {e}")
            
            # Kein Screenshot gefunden
            text_item = self.screenshot_scene.addText("Kein Screenshot verfügbar")
            text_item.setPos(10, 10)
            
        except Exception as e:
            print(f"Fehler beim Laden des Screenshots: {e}")
            text_item = self.screenshot_scene.addText("Fehler beim Laden des Screenshots")
            text_item.setPos(10, 10)
    
    def add_element_overlays(self):
        """Element-Overlays hinzufügen (wie in HTML)"""
        try:
            # Durchsuche alle Elemente nach Geometrie
            for elem in self.xml_data.iter():
                if elem.tag == 'element':
                    # Suche abstractProperties/geometry
                    abstract_props = elem.find('abstractProperties')
                    if abstract_props is not None:
                        geometry = abstract_props.find('geometry')
                        if geometry is not None:
                            self.create_element_overlay(geometry, elem)
        except Exception as e:
            print(f"Fehler beim Erstellen der Overlays: {e}")
    
    def create_element_overlay(self, geometry, element):
        """Element-Overlay erstellen"""
        try:
            x_elem = geometry.find('x')
            y_elem = geometry.find('y')
            w_elem = geometry.find('width')
            h_elem = geometry.find('height')
            
            if all(e is not None and e.text for e in [x_elem, y_elem, w_elem, h_elem]):
                x = float(x_elem.text) * self.image_scale_factor
                y = float(y_elem.text) * self.image_scale_factor
                w = float(w_elem.text) * self.image_scale_factor
                h = float(h_elem.text) * self.image_scale_factor
                
                if w > 2 and h > 2:
                    # Rotes Overlay-Rechteck (wie in HTML)
                    pen = QPen(QColor('red'))
                    pen.setWidth(2)
                    brush = QBrush(QColor(255, 0, 0, 30))  # Transparentes Rot
                    
                    rect_item = self.screenshot_scene.addRect(x, y, w, h, pen, brush)
                    
                    # Tooltip mit Element-Info
                    simplified_type = element.get('simplifiedType', '')
                    class_name = element.get('class', '')
                    tooltip = simplified_type or class_name or 'Element'
                    rect_item.setToolTip(tooltip)
        
        except (ValueError, AttributeError) as e:
            print(f"Fehler beim Erstellen des Overlays: {e}")
    
    def on_tree_selection_changed(self):
        """Tree-Auswahl geändert"""
        current_item = self.tree_widget.currentItem()
        if current_item:
            xml_element = current_item.data(0, Qt.UserRole)
            if xml_element is not None:
                self.update_properties(xml_element)
    
    def update_properties(self, xml_element):
        """Properties-Tabelle aktualisieren - vollständiges Parsing"""
        self.properties_table.setRowCount(0)
        
        properties = []
        
        # Element-Attribute
        if xml_element.attrib:
            for attr_name, attr_value in xml_element.attrib.items():
                properties.append(("Attributes", attr_name, str(attr_value)))
        
        # Properties aus <properties>
        props_elem = xml_element.find('properties')
        if props_elem is not None:
            for prop in props_elem.findall('property'):
                prop_name = prop.get('name', '')
                prop_value = prop.text
                if prop_value is None:
                    # Suche nach string-Element
                    string_elem = prop.find('string')
                    if string_elem is not None:
                        prop_value = string_elem.text or ""
                    else:
                        # Suche nach anderen Untertypen
                        for child in prop:
                            if child.text:
                                prop_value = child.text
                                break
                        else:
                            prop_value = ""
                properties.append(("Properties", prop_name, str(prop_value or "")))
        
        # Abstract Properties
        abstract_props = xml_element.find('abstractProperties')
        if abstract_props is not None:
            for child in abstract_props:
                if child.tag == 'geometry':
                    for geom_child in child:
                        properties.append(("Geometry", geom_child.tag, str(geom_child.text or "")))
                else:
                    properties.append(("Abstract", child.tag, str(child.text or "")))
        
        # Direkte Kinder-Elemente
        for child in xml_element:
            if child.tag not in ['properties', 'abstractProperties', 'children', 'element']:
                if child.text and child.text.strip():
                    properties.append(("Element", child.tag, str(child.text)))
                else:
                    # Sub-Elemente
                    for subchild in child:
                        if subchild.text and subchild.text.strip():
                            properties.append(("Element", f"{child.tag}.{subchild.tag}", str(subchild.text)))
        
        # Sortieren basierend auf Auswahl
        sort_order = self.sort_combo.currentText()
        if sort_order == "A→Z":
            properties.sort(key=lambda x: x[1])
        elif sort_order == "Z→A":
            properties.sort(key=lambda x: x[1], reverse=True)
        
        # Tabelle füllen
        self.properties_table.setRowCount(len(properties))
        self.properties_table.setVerticalHeaderLabels([str(i+1) for i in range(len(properties))])
        
        for i, (group, name, value) in enumerate(properties):
            name_item = QTableWidgetItem(str(name))
            value_item = QTableWidgetItem(str(value))
            
            # Zeilenfarbe basierend auf Gruppe
            if group == "Attributes":
                name_item.setBackground(QColor('#e3f2fd'))
            elif group == "Geometry":
                name_item.setBackground(QColor('#f3e5f5'))
            
            self.properties_table.setItem(i, 0, name_item)
            self.properties_table.setItem(i, 1, value_item)
    
    def refresh_properties(self):
        """Properties mit neuer Sortierung aktualisieren"""
        current_item = self.tree_widget.currentItem()
        if current_item:
            xml_element = current_item.data(0, Qt.UserRole)
            if xml_element is not None:
                self.update_properties(xml_element)
    
    def filter_tree(self):
        """Tree filtern"""
        search_text = self.tree_search.text().lower()
        if not search_text:
            # Alle Items anzeigen
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                self.show_all_items(item)
        else:
            # Items filtern
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                self.filter_item(item, search_text)
    
    def show_all_items(self, item):
        """Alle Items anzeigen (rekursiv)"""
        item.setHidden(False)
        for i in range(item.childCount()):
            self.show_all_items(item.child(i))
    
    def filter_item(self, item, search_text):
        """Item filtern (rekursiv)"""
        # Prüfe ob der Text im aktuellen Item vorkommt
        match = search_text in item.text(0).lower()
        
        # Prüfe Kinder
        child_match = False
        for i in range(item.childCount()):
            if self.filter_item(item.child(i), search_text):
                child_match = True
        
        # Item anzeigen wenn Match oder Kinder-Match
        visible = match or child_match
        item.setHidden(not visible)
        
        return visible
    
    def filter_properties(self):
        """Properties filtern"""
        search_text = self.props_search.text().lower()
        
        for i in range(self.properties_table.rowCount()):
            prop_name = self.properties_table.item(i, 0).text().lower()
            prop_value = self.properties_table.item(i, 1).text().lower()
            
            visible = search_text in prop_name or search_text in prop_value
            self.properties_table.setRowHidden(i, not visible)
    
    def show_tree_context_menu(self, position):
        """Kontextmenü für Tree anzeigen"""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu()
            
            copy_name = QAction("Element-Name kopieren", self)
            copy_name.triggered.connect(lambda: self.copy_tree_data("name"))
            menu.addAction(copy_name)
            
            copy_class = QAction("Element-Klasse kopieren", self)
            copy_class.triggered.connect(lambda: self.copy_tree_data("class"))
            menu.addAction(copy_class)
            
            copy_id = QAction("Element-ID kopieren", self)
            copy_id.triggered.connect(lambda: self.copy_tree_data("id"))
            menu.addAction(copy_id)
            
            menu.exec_(self.tree_widget.mapToGlobal(position))
    
    def show_properties_context_menu(self, position):
        """Kontextmenü für Properties anzeigen"""
        item = self.properties_table.itemAt(position)
        if item:
            menu = QMenu()
            
            copy_prop = QAction("Property kopieren", self)
            copy_prop.triggered.connect(lambda: self.copy_property_data("name"))
            menu.addAction(copy_prop)
            
            copy_value = QAction("Value kopieren", self)
            copy_value.triggered.connect(lambda: self.copy_property_data("value"))
            menu.addAction(copy_value)
            
            copy_both = QAction("Property=Value kopieren", self)
            copy_both.triggered.connect(lambda: self.copy_property_data("both"))
            menu.addAction(copy_both)
            
            menu.exec_(self.properties_table.mapToGlobal(position))
    
    def copy_tree_data(self, copy_type):
        """Tree-Daten kopieren"""
        current_item = self.tree_widget.currentItem()
        if not current_item:
            return
        
        xml_element = current_item.data(0, Qt.UserRole)
        copied_text = ""
        
        if copy_type == "name":
            copied_text = current_item.text(0)
        elif copy_type == "class" and xml_element is not None:
            copied_text = xml_element.get('class', '')
        elif copy_type == "id" and xml_element is not None:
            copied_text = xml_element.get('id', '')
        
        if copied_text:
            QApplication.clipboard().setText(copied_text)
            self.toast.show_toast(f"Kopiert: {copied_text[:50]}{'...' if len(copied_text) > 50 else ''}")
    
    def copy_property_data(self, copy_type):
        """Property-Daten kopieren"""
        current_row = self.properties_table.currentRow()
        if current_row < 0:
            return
        
        prop_name = self.properties_table.item(current_row, 0).text()
        prop_value = self.properties_table.item(current_row, 1).text()
        
        copied_text = ""
        if copy_type == "name":
            copied_text = prop_name
        elif copy_type == "value":
            copied_text = prop_value
        elif copy_type == "both":
            copied_text = f"{prop_name}={prop_value}"
        
        if copied_text:
            QApplication.clipboard().setText(copied_text)
            self.toast.show_toast(f"Kopiert: {copied_text[:50]}{'...' if len(copied_text) > 50 else ''}")
    
    def reload_file(self):
        """Aktuelle Datei neu laden"""
        if self.current_file:
            self.load_xml_file(self.current_file)
        else:
            QMessageBox.information(self, "Info", "Keine Datei zum Neuladen geöffnet")
    
    def close_file(self):
        """Datei schließen"""
        self.current_file = None
        self.xml_data = None
        self.tree_widget.clear()
        self.properties_table.setRowCount(0)
        self.screenshot_scene.clear()
        self.setWindowTitle("Object Viewer")
        self.statusBar().showMessage("Bereit")


def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # Clean, minimal styling - GitHub-inspired
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ffffff;
        }
        
        /* Toast Notifications */
        QLabel {
            font-size: 14px;
        }
        
        /* Tooltips */
        QToolTip {
            background-color: #24292e;
            color: white;
            border: 1px solid #444d56;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
        }
        
        /* Clean Scroll Bars */
        QScrollBar:vertical {
            border: none;
            background: #f6f8fa;
            width: 14px;
        }
        QScrollBar::handle:vertical {
            background: #d1d5da;
            border-radius: 7px;
            min-height: 30px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: #586069;
        }
        
        QScrollBar:horizontal {
            border: none;
            background: #f6f8fa;
            height: 14px;
        }
        QScrollBar::handle:horizontal {
            background: #d1d5da;
            border-radius: 7px;
            min-width: 30px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #586069;
        }
        
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
    """)
    
    viewer = SquishXMLDesktopViewer()
    viewer.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()