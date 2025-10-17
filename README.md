# Squish Snapshot Viewer

Ein Cross-Platform Desktop-Viewer für Squish XML-Snapshots mit moderner Benutzeroberfläche.

## 🚀 Features

- **🌍 Cross-Platform** - macOS, Linux, Windows
- **📱 Modern UI** - Native Menüs und plattformoptimierte Bedienung
- **🔍 Interactive Viewer** - Tree, Screenshot und Properties Panel
- **📋 Context Menus** - Einfaches Kopieren von Properties
- **🌐 WebView Integration** - HTML/CSS/JS basierte Darstellung

## 📦 Installation

1. **Repository klonen:**
   ```bash
   git clone <your-repo-url>
   cd squish_snapshot_viewer
   ```

2. **Dependencies installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Anwendung starten:**
   ```bash
   python3 squish_snapshot_viewer.py
   ```

## 🎯 Verwendung

### XML-Dateien laden
- **Einzelne Datei**: `Ctrl+O` (Cmd+O auf macOS)
- **Ganzer Ordner**: `Ctrl+Shift+O`
- **Command-Line**: `python3 squish_snapshot_viewer.py pfad/zur/datei.xml`

### Navigation
- **Tree-Ansicht** (links): Objekthierarchie durchsuchen
- **Screenshot** (oben rechts): UI-Screenshot mit Element-Overlays
- **Properties** (unten rechts): Eigenschaften des ausgewählten Elements

### Tastenkürzel
| Shortcut | Funktion |
|----------|----------|
| `Ctrl+O` | XML-Datei öffnen |
| `Ctrl+Shift+O` | Ordner öffnen |
| `Ctrl+L` | Liste leeren |
| `F5` | WebView neu laden |
| `Ctrl+B` | In externem Browser öffnen |
| `Ctrl+Q` | Beenden |

## 🛠️ Systemanforderungen

- **Python 3.8+**
- **PyQt5** mit WebEngine
- **Alle Plattformen**: Windows, macOS, Linux

## 📁 Projektstruktur

```
squish_snapshot_viewer/
├── squish_snapshot_viewer.py    # Hauptanwendung
├── requirements.txt             # Python Dependencies
└── README.md                   # Diese Dokumentation
```

## 🐛 Troubleshooting

### "No module named PyQt5"
```bash
pip install PyQt5 PyQtWebEngine
```

### Ubuntu/Debian System-Pakete (alternative)
```bash
sudo apt install python3-pyqt5 python3-pyqt5.qtwebengine
```

### Virtual Environment (empfohlen)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# oder: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
python3 squish_snapshot_viewer.py
```

## 📄 Lizenz

MIT License

---

**Viel Spaß mit dem Squish Snapshot Viewer! 🎉**