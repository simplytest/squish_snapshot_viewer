
# Squish Snapshot Viewer

Dieses Tool dient zur visuellen Anzeige und Analyse von Squish Snapshot XML-Dateien direkt im Browser. Die Oberfläche ist vollständig webbasiert und benötigt keine Python-Installation.

## Features

- **Datei- und Ordnerauswahl**: Wähle einen Ordner mit XML-Snapshots aus, die Dateien werden links als Liste angezeigt.
- **Objektbaum**: Die XML-Hierarchie wird als interaktiver, ausklappbarer Baum dargestellt. Doppelklick auf die Baum-Überschrift expandiert/kollabiert alle Knoten.
- **Screenshot-Anzeige**: Das im Snapshot eingebettete PNG-Bild wird angezeigt. Über einen Zoom-Slider kann die Ansicht skaliert werden.
- **Element-Highlighting**: Ein Klick ins Screenshot-Bild wählt das kleinste passende Element im Baum aus und hebt es visuell hervor.
- **Eigenschaftentabelle**: Die Eigenschaften des gewählten Elements werden als sortierbare Tabelle angezeigt. Rechtsklick auf eine Eigenschaft öffnet ein Kontextmenü zum Kopieren von Name oder Wert.
- **Kontextmenüs**: Im Baum und in der Eigenschaftentabelle stehen Kontextmenüs zum schnellen Kopieren von Namen, Typen oder Objekt-Strings zur Verfügung.
- **Suche & Filter**: Es gibt separate Suchfelder für Baum, Eigenschaften und Werte. Treffer werden gelb markiert, optional können nur passende Knoten angezeigt werden.
- **Layout & Theme**: Die Ansicht kann zwischen "Side-by-side" und gestapeltem Layout umgeschaltet werden. Mehrere Farbschemata stehen zur Auswahl.
- **Hilfe-Popup**: Über das Fragezeichen rechts oben öffnet sich ein Hilfe-Fenster mit Erläuterungen zur Bedienung.

## Bedienung

1. Öffne die `viewer.html` im Browser (empfohlen: Chrome, Edge, Firefox).
2. Wähle über "Select Folder" einen Ordner mit Squish XML-Snapshots aus.
3. Klicke auf eine Datei in der Liste, um sie zu laden.
4. Navigiere im Objektbaum, klicke auf Knoten für Details und nutze die Kontextmenüs.
5. Über das Screenshot-Bild kannst du Elemente direkt auswählen und hervorheben.
6. Nutze die Suchfelder und Layout-/Theme-Optionen für eine individuelle Ansicht.
7. Die Hilfe ist jederzeit über das Fragezeichen erreichbar.

## Hinweise

- Es werden ausschließlich XML-Dateien mit Squish-Snapshot-Struktur unterstützt.
- Die Anwendung läuft komplett lokal im Browser, es werden keine Daten übertragen.
- Für Feedback oder Fragen siehe Hilfe-Popup.

---

**Entwickelt für die schnelle visuelle Analyse von Squish Snapshots.**