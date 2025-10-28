This is a command-line tool that generates an HTML report for viewing and inspecting Squish XML snapshot files in a web browser.

## Features

- **Tree View**: Displays the complete object hierarchy from the Squish snapshot in a collapsible tree structure.
- **Property Inspector**: Click on any element in the tree to view its properties, including attributes, geometry, and visual information.
- **Embedded Screenshot**: Shows the screenshot that was captured with the snapshot.
- **File Loading**:
  - Load a file from the command line: `python show_snap.py <path_to_file.xml>`.
- **Interactive Element Highlighting**: Clicking on an element in the screenshot will now highlight the smallest element at that position in the object tree and display its properties.

## Recent Improvements

- **Refactored Asset Loading**: CSS, JavaScript, and HTML template files are now loaded directly from external files at runtime, improving maintainability and development workflow.
- **Enhanced Security & Reliability**: Replaced potentially unsafe `eval()` calls with `JSON.parse()` in JavaScript assets for better security and more robust JSON parsing.
- **Improved Visual Feedback**: Adjusted the pulsing animation for highlighted elements to provide a more uniform and noticeable visual effect across different element sizes. 

## Installation

1. Clone the repository or download the source code.
2. Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

To run the application, execute the following command from your terminal:

```bash
python show_snap.py
```

### Opening Files

- **From the Command Line**: You can open an XML file directly by passing its path as a command-line argument:

```bash
  python show_snap.py /path/to/your/snapshot.xml
```

  If no file is specified, the program will interactively prompt you to select an XML file from the current directory or a specified directory.

### Interacting with the Viewer

- **Object Tree**: Navigate the object hierarchy on the left panel. Click the arrows to expand or collapse child elements.
- **Properties**: Click on an object name in the tree. Its properties will be displayed in the "Properties" panel on the right.
- **Screenshot**: The captured screenshot is shown in the top right panel. Clicking on an element in the screenshot will highlight the smallest element at that position in the object tree.