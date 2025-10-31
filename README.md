
# Squish Snapshot Viewer

A browser-based tool for visual display and analysis of Squish Snapshot XML files. The interface is completely web-based and requires no Python installation.

## Features

- **File and Folder Selection**: Choose a folder with XML snapshots, files are displayed as a list on the left.
- **Object Tree**: The XML hierarchy is presented as an interactive, expandable tree. Double-click on the tree header expands/collapses all nodes.
- **Screenshot Display**: The embedded PNG image in the snapshot is displayed. Use the zoom slider to scale the view.
- **Element Highlighting**: Clicking on the screenshot selects the smallest matching element in the tree and highlights it visually.
- **Properties Table**: Properties of the selected element are displayed as a sortable table. Right-click on a property opens a context menu for copying name or value.
- **Context Menus**: Context menus in the tree and properties table allow quick copying of names, types, or object strings.
- **Search & Filter**: Separate search fields for tree, properties, and values. Matches are highlighted in yellow, with an option to show only matching nodes.
- **Layout & Theme**: Switch between "Side-by-side" and stacked layout. Multiple color schemes are available.
- **Help Popup**: Click the question mark in the top right to open a help window with usage instructions and release notes.

## Usage

1. Open `viewer.html` in your browser (recommended: Chrome, Edge, Firefox).
2. Select a folder with Squish XML snapshots using "Select Folder".
3. Click on a file in the list to load it.
4. Navigate the object tree, click on nodes for details, and use the context menus.
5. Use the screenshot to directly select and highlight elements.
6. Use the search fields and layout/theme options for a customized view.
7. Access help anytime via the question mark icon.

## Notes

- Only XML files with Squish snapshot structure are supported.
- The application runs completely locally in the browser; no data is transmitted.
- For feedback or questions, see the Help popup.

## Latest Updates

- Harmonized UI spacing
- Implemented overlay recalculation on window resize
- Added BasePage element menu generation
- Improved navigation with automatic scrolling to highlighted elements
- Enhanced element selection highlighting

---

**Developed for quick visual analysis of Squish snapshots.**