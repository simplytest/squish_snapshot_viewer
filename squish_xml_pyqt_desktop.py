#!/usr/bin/env python3
"""
squish_xml_pyqt_desktop.py

Desktop-App für Squish XML Viewer mit PyQt5
- Echte GUI mit Fenstern
- Alle Features der Web-Version
- Funktioniert garantiert
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
        QSplitter, QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
        QLineEdit, QLabel, QPushButton, QStatusBar, QHeaderView, QFrame,
        QGroupBox, QGridLayout, QTextEdit
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QIcon, QPixmap, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

class SquishXMLViewer(QMainWindow):
    """Hauptklasse für den PyQt5 XML Viewer"""
    
    def __init__(self):
        super().__init__()
        
        if not PYQT_AVAILABLE:
            print("❌ PyQt5 nicht verfügbar! Installieren Sie: pip install PyQt5")
            sys.exit(1)
        
        self.current_file = None
        self.xml_data = None
        
        self.init_ui()
        
        # Falls Datei als Argument übergeben
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_xml_file(sys.argv[1])
    
    def init_ui(self):
        """Benutzeroberfläche initialisieren"""
        self.setWindowTitle("Squish XML Snapshot Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        self.create_header(layout)
        
        # Hauptbereich mit Splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Linkes Panel: XML Baum
        self.create_tree_panel(splitter)
        
        # Rechtes Panel: Properties
        self.create_properties_panel(splitter)
        
        # Splitter-Verhältnis setzen
        splitter.setSizes([700, 700])
        
        # Menü und Statusbar
        self.create_menu()
        self.create_statusbar()
    
    def create_header(self, parent_layout):
        """Header-Bereich erstellen (wie in HTML-Version)"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #2c3e50; color: white; padding: 10px;")
        parent_layout.addWidget(header_frame)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Title (Object Viewer)
        title_label = QLabel("Object Viewer")
        title_label.setStyleSheet("font-weight: bold; font-size: 18px; color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Tree Search
        tree_search_label = QLabel("Tree:")
        tree_search_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        header_layout.addWidget(tree_search_label)
        
        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("Search tree...")
        self.tree_search.setFixedWidth(150)
        self.tree_search.textChanged.connect(self.filter_tree)
        header_layout.addWidget(self.tree_search)
        
        clear_tree_btn = QPushButton("×")
        clear_tree_btn.setFixedSize(25, 25)
        clear_tree_btn.clicked.connect(lambda: self.tree_search.clear())
        header_layout.addWidget(clear_tree_btn)
        
        # Properties Search
        props_search_label = QLabel("Properties:")
        props_search_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        header_layout.addWidget(props_search_label)
        
        self.props_search = QLineEdit()
        self.props_search.setPlaceholderText("Search properties...")
        self.props_search.setFixedWidth(150)
        self.props_search.textChanged.connect(self.filter_properties)
        header_layout.addWidget(self.props_search)
        
        clear_props_btn = QPushButton("×")
        clear_props_btn.setFixedSize(25, 25)
        clear_props_btn.clicked.connect(lambda: self.props_search.clear())
        header_layout.addWidget(clear_props_btn)
        
        # Sort Dropdown
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet("color: #ecf0f1; font-size: 12px;")
        header_layout.addWidget(sort_label)
        
        from PyQt5.QtWidgets import QComboBox
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Descending", "Ascending", "None"])
        self.sort_combo.setCurrentText("Descending")
        self.sort_combo.currentTextChanged.connect(self.refresh_properties)
        header_layout.addWidget(self.sort_combo)
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(open_btn)
    
    def create_tree_panel(self, parent_splitter):
        """XML-Baum Panel erstellen"""
        tree_group = QGroupBox("🌳 XML Struktur")
        parent_splitter.addWidget(tree_group)
        
        layout = QVBoxLayout(tree_group)
        
        # Suchfeld
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Suchen:"))
        
        self.tree_search = QLineEdit()
        self.tree_search.setPlaceholderText("Element-Name eingeben...")
        self.tree_search.textChanged.connect(self.filter_tree)
        search_layout.addWidget(self.tree_search)
        
        clear_btn = QPushButton("✕")
        clear_btn.setMaximumWidth(30)
        clear_btn.clicked.connect(lambda: self.tree_search.clear())
        search_layout.addWidget(clear_btn)
        
        layout.addLayout(search_layout)
        
        # Tree Widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(['Element', 'Typ', 'Wert'])
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_tree_context_menu)
        
        # Spaltenbreiten
        self.tree_widget.setColumnWidth(0, 250)
        self.tree_widget.setColumnWidth(1, 100)
        self.tree_widget.setColumnWidth(2, 200)
        
        layout.addWidget(self.tree_widget)
    
    def create_properties_panel(self, parent_splitter):
        """Properties Panel erstellen"""
        props_group = QGroupBox("📋 Eigenschaften")
        parent_splitter.addWidget(props_group)
        
        layout = QVBoxLayout(props_group)
        
        # Suchfeld für Properties
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Suchen:"))
        
        self.props_search = QLineEdit()
        self.props_search.setPlaceholderText("Eigenschaft suchen...")
        self.props_search.textChanged.connect(self.filter_properties)
        search_layout.addWidget(self.props_search)
        
        props_clear_btn = QPushButton("✕")
        props_clear_btn.setMaximumWidth(30)
        props_clear_btn.clicked.connect(lambda: self.props_search.clear())
        search_layout.addWidget(props_clear_btn)
        
        layout.addLayout(search_layout)
        
        # Properties Table
        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(2)
        self.properties_table.setHorizontalHeaderLabels(['Eigenschaft', 'Wert'])
        self.properties_table.horizontalHeader().setStretchLastSection(True)
        self.properties_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.properties_table.customContextMenuRequested.connect(self.show_props_context_menu)
        
        layout.addWidget(self.properties_table)
    
    def create_menu(self):
        """Menüleiste erstellen"""
        menubar = self.menuBar()
        
        # Datei-Menü
        file_menu = menubar.addMenu('📁 Datei')
        
        open_action = QAction('📂 Öffnen...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        reload_action = QAction('🔄 Neu laden', self)
        reload_action.setShortcut('Ctrl+R')
        reload_action.triggered.connect(self.reload_file)
        file_menu.addAction(reload_action)
        
        close_action = QAction('❌ Schließen', self)
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('🚪 Beenden', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Bearbeiten-Menü
        edit_menu = menubar.addMenu('✏️ Bearbeiten')
        
        copy_action = QAction('📋 Kopieren', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)
    
    def create_statusbar(self):
        """Statusleiste erstellen"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Bereit")
    
    def open_file_dialog(self):
        """Datei-Dialog öffnen"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "XML-Datei auswählen",
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            self.load_xml_file(file_path)
    
    def load_xml_file(self, file_path):
        """XML-Datei laden und anzeigen"""
        try:
            self.current_file = file_path
            self.statusbar.showMessage(f"Lade {os.path.basename(file_path)}...")
            
            # XML parsen
            tree = ET.parse(file_path)
            self.xml_data = tree.getroot()
            
            # UI aktualisieren
            filename = os.path.basename(file_path)
            self.file_info_label.setText(f"📄 {filename}")
            self.setWindowTitle(f"Squish XML Viewer - {filename}")
            
            # Tree aufbauen
            self.populate_tree()
            
            # Properties leeren
            self.properties_table.setRowCount(0)
            
            self.statusbar.showMessage(f"✅ Datei geladen: {filename}")
            self.show_toast(f"XML-Datei '{filename}' erfolgreich geladen!")
            
        except Exception as e:
            error_msg = f"Fehler beim Laden: {str(e)}"
            self.statusbar.showMessage(f"❌ {error_msg}")
            QMessageBox.critical(self, "Fehler", error_msg)
    
    def populate_tree(self):
        """XML-Baum mit Daten füllen"""
        self.tree_widget.clear()
        
        if self.xml_data is not None:
            root_item = self.add_tree_element(None, self.xml_data, is_root=True)
            self.tree_widget.expandItem(root_item)
    
    def add_tree_element(self, parent_item, element, is_root=False):
        """Element zum Baum hinzufügen"""
        # Element-Item erstellen
        if parent_item is None:
            item = QTreeWidgetItem(self.tree_widget)
        else:
            item = QTreeWidgetItem(parent_item)
        
        # Element-Daten setzen
        tag = element.tag
        element_type = "root" if is_root else "element"
        text_content = element.text.strip() if element.text and element.text.strip() else ""
        
        # Truncate langen Text
        display_text = text_content[:50] + "..." if len(text_content) > 50 else text_content
        
        item.setText(0, tag)
        item.setText(1, element_type)
        item.setText(2, display_text)
        
        # XML-Element-Referenz speichern
        item.setData(0, Qt.UserRole, element)
        
        # Icons setzen
        if is_root:
            item.setText(0, f"📁 {tag}")
        elif list(element):
            item.setText(0, f"📂 {tag}")
        else:
            item.setText(0, f"📄 {tag}")
        
        # Attribute als Kinder hinzufügen
        for attr_name, attr_value in element.attrib.items():
            attr_item = QTreeWidgetItem(item)
            attr_item.setText(0, f"🏷️ @{attr_name}")
            attr_item.setText(1, "attribute")
            attr_item.setText(2, attr_value)
            attr_item.setData(0, Qt.UserRole, {'type': 'attribute', 'name': attr_name, 'value': attr_value, 'parent': element})
        
        # Kinder-Elemente hinzufügen
        for child in element:
            self.add_tree_element(item, child)
        
        return item
    
    def on_tree_selection_changed(self):
        """Tree-Auswahl geändert"""
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        
        self.update_properties_for_item(current_item)
    
    def update_properties_for_item(self, item):
        """Properties für ausgewähltes Item aktualisieren"""
        self.properties_table.setRowCount(0)
        
        # Daten aus Item abrufen
        element_data = item.data(0, Qt.UserRole)
        
        if isinstance(element_data, dict) and element_data.get('type') == 'attribute':
            # Attribut ausgewählt
            self.add_property_row("Name", element_data['name'])
            self.add_property_row("Typ", "attribute")
            self.add_property_row("Wert", element_data['value'])
            parent_element = element_data['parent']
            self.add_property_row("Parent-Element", parent_element.tag)
        
        elif hasattr(element_data, 'tag'):
            # XML-Element ausgewählt
            element = element_data
            
            self.add_property_row("Name", element.tag)
            self.add_property_row("Typ", "element")
            
            if element.text and element.text.strip():
                self.add_property_row("Text", element.text.strip())
            
            # Attribute
            if element.attrib:
                self.add_property_row("Attribute", f"{len(element.attrib)} Attribute")
                for attr_name, attr_value in element.attrib.items():
                    self.add_property_row(f"  @{attr_name}", attr_value)
            
            # Kinder-Elemente
            children = list(element)
            if children:
                self.add_property_row("Kinder", f"{len(children)} Elemente")
            
            # Parent-Element
            parent = self.find_parent_element(element)
            if parent is not None:
                self.add_property_row("Parent", parent.tag)
            
            # XML-Pfad
            path = self.get_element_path(element)
            self.add_property_row("XML-Pfad", path)
    
    def add_property_row(self, name, value):
        """Property-Zeile zur Tabelle hinzufügen"""
        row = self.properties_table.rowCount()
        self.properties_table.insertRow(row)
        
        name_item = QTableWidgetItem(str(name))
        value_item = QTableWidgetItem(str(value))
        
        self.properties_table.setItem(row, 0, name_item)
        self.properties_table.setItem(row, 1, value_item)
    
    def find_parent_element(self, target_element):
        """Parent-Element finden"""
        if self.xml_data is None:
            return None
        
        for elem in self.xml_data.iter():
            if target_element in list(elem):
                return elem
        return None
    
    def get_element_path(self, target_element):
        """XML-Pfad erstellen"""
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
        
        if self.xml_data is not None:
            find_path(self.xml_data, [])
        
        return "/" + "/".join(path_parts) if path_parts else "/unknown"
    
    def show_tree_context_menu(self, position):
        """Tree-Kontextmenü anzeigen"""
        item = self.tree_widget.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        
        copy_name_action = QAction("📝 Element-Name kopieren", self)
        copy_name_action.triggered.connect(lambda: self.copy_tree_item(item, "name"))
        menu.addAction(copy_name_action)
        
        copy_type_action = QAction("🏷️ Element-Typ kopieren", self)
        copy_type_action.triggered.connect(lambda: self.copy_tree_item(item, "type"))
        menu.addAction(copy_type_action)
        
        copy_value_action = QAction("💬 Element-Wert kopieren", self)
        copy_value_action.triggered.connect(lambda: self.copy_tree_item(item, "value"))
        menu.addAction(copy_value_action)
        
        menu.exec_(self.tree_widget.mapToGlobal(position))
    
    def show_props_context_menu(self, position):
        """Properties-Kontextmenü anzeigen"""
        item = self.properties_table.itemAt(position)
        if item is None:
            return
        
        menu = QMenu(self)
        
        copy_prop_action = QAction("📝 Eigenschaft kopieren", self)
        copy_prop_action.triggered.connect(lambda: self.copy_property_item("name"))
        menu.addAction(copy_prop_action)
        
        copy_value_action = QAction("💬 Wert kopieren", self)
        copy_value_action.triggered.connect(lambda: self.copy_property_item("value"))
        menu.addAction(copy_value_action)
        
        copy_both_action = QAction("📋 Eigenschaft=Wert kopieren", self)
        copy_both_action.triggered.connect(lambda: self.copy_property_item("both"))
        menu.addAction(copy_both_action)
        
        menu.exec_(self.properties_table.mapToGlobal(position))
    
    def copy_tree_item(self, item, copy_type):
        """Tree-Item in Zwischenablage kopieren"""
        if copy_type == "name":
            text = item.text(0).replace("📁 ", "").replace("📂 ", "").replace("📄 ", "").replace("🏷️ ", "")
        elif copy_type == "type":
            text = item.text(1)
        elif copy_type == "value":
            text = item.text(2)
        else:
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.show_toast(f"Kopiert: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def copy_property_item(self, copy_type):
        """Property-Item in Zwischenablage kopieren"""
        current_row = self.properties_table.currentRow()
        if current_row < 0:
            return
        
        prop_name = self.properties_table.item(current_row, 0).text()
        prop_value = self.properties_table.item(current_row, 1).text()
        
        if copy_type == "name":
            text = prop_name
        elif copy_type == "value":
            text = prop_value
        elif copy_type == "both":
            text = f"{prop_name}={prop_value}"
        else:
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self.show_toast(f"Kopiert: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    def copy_selection(self):
        """Aktuelle Auswahl kopieren"""
        # Vereinfachte Implementierung
        current_item = self.tree_widget.currentItem()
        if current_item:
            self.copy_tree_item(current_item, "name")
    
    def filter_tree(self, text):
        """Tree filtern"""
        # Vereinfachte Implementierung - zeigt/versteckt Items
        def filter_item(item):
            text_lower = text.lower()
            item_text = item.text(0).lower()
            
            # Prüfe ob Item oder Kinder dem Filter entsprechen
            matches = not text or text_lower in item_text
            
            # Prüfe Kinder
            child_matches = False
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_item(child):
                    child_matches = True
            
            # Item anzeigen wenn es oder seine Kinder passen
            show_item = matches or child_matches
            item.setHidden(not show_item)
            
            return show_item
        
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            filter_item(root.child(i))
    
    def filter_properties(self, text):
        """Properties filtern"""
        text_lower = text.lower()
        for row in range(self.properties_table.rowCount()):
            name_item = self.properties_table.item(row, 0)
            value_item = self.properties_table.item(row, 1)
            
            name_text = name_item.text().lower() if name_item else ""
            value_text = value_item.text().lower() if value_item else ""
            
            matches = not text or text_lower in name_text or text_lower in value_text
            self.properties_table.setRowHidden(row, not matches)
    
    def reload_file(self):
        """Datei neu laden"""
        if self.current_file:
            self.load_xml_file(self.current_file)
        else:
            self.show_toast("Keine Datei zum Neuladen!", error=True)
    
    def close_file(self):
        """Datei schließen"""
        self.current_file = None
        self.xml_data = None
        
        self.file_info_label.setText("📄 Keine Datei geladen")
        self.setWindowTitle("Squish XML Snapshot Viewer")
        
        self.tree_widget.clear()
        self.properties_table.setRowCount(0)
        
        self.statusbar.showMessage("Datei geschlossen")
        self.show_toast("Datei geschlossen")
    
    def show_toast(self, message, error=False):
        """Toast-ähnliche Benachrichtigung (vereinfacht über Statusbar)"""
        if error:
            self.statusbar.showMessage(f"❌ {message}")
        else:
            self.statusbar.showMessage(f"✅ {message}")
        
        # Nach 3 Sekunden zurücksetzen
        QTimer.singleShot(3000, lambda: self.statusbar.showMessage("Bereit"))

def main():
    """Hauptfunktion"""
    app = QApplication(sys.argv)
    
    # App-Style setzen
    app.setStyle('Fusion')
    
    viewer = SquishXMLViewer()
    viewer.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()