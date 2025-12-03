
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
- **Navigation Breadcrumb**: Interactive breadcrumb shows the path to the selected element. Click on parent elements to navigate the tree hierarchy.
- **Layout & Theme**: Switch between "Side-by-side" and stacked layout. Multiple color schemes are available.
- **Help Popup**: Click the question mark in the top right to open a help window with usage instructions and release notes.

## Installation

### Download on Ubuntu

Download the viewer using curl:
```bash
curl -O https://raw.githubusercontent.com/simplytest/squish_snapshot_viewer/master/viewer.html
```

Or using wget:
```bash
wget https://raw.githubusercontent.com/simplytest/squish_snapshot_viewer/master/viewer.html
```

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

## Release Notes

### v1.5.0
- New. Interactive Navigation Breadcrumb with hierarchical path display
- New. Smart text truncation for breadcrumb elements using CamelCase intelligence
- New. Responsive breadcrumb design adapting to available screen space
- New. Improved "Only Matches" filter behavior with better tree visibility control
- Fix. Breadcrumb layout stability when selecting root elements

### v1.4.0
- New. Resizable Splitter for Object Tree
- New. Context menu for element overlay
- New. Extended properties context menu with node actions
- New. Added Expand/Collapse All button for Object Tree
- New. Added "Copy Path" to context menus
- Fix. Improved element selection and highlighting behavior

### v1.3.0
- Fix. Harmonized UI spacing
- Fix. Implemented overlay recalculation on window resize
- New. Added BasePage element menu generation with recurision to parent if more then one container found
- New. Improved navigation with automatic scrolling to highlighted elements in object tree
- New. Enhanced element selection highlighting

### v1.2.1
- New. Zoom factor check boxes and theme are now persistent

### v1.2.0
- New. Added Help page with self-contained Base64 pictures

### v1.1.2
- New. Added zoom factor for pictures and overlays
- New. Added File List collapsable

### v1.1.1
- Fix. Scrollable card areas
- Fix. Better height handling
- New. Added themes support

### v1.1.0
- Fix. Layout improvements

### v1.0.0
- New. Initial version with Object Tree, Snapshot view, and Properties

---

**Developed for quick visual analysis of Squish snapshots.**