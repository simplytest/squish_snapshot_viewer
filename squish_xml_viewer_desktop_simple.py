#!/usr/bin/env python3
"""
squish_xml_viewer_desktop_simple.py

Simple desktop version of squish_xml_viewer.py using pywebview
Generates desktop application with:
 - embedded screenshot (if present in XML)
 - object tree from XML structure
 - properties for selected node
 - click-to-highlight overlay functionality

Usage:
    python3 squish_xml_viewer_desktop_simple.py path/to/snapshot.xml
"""

import sys
import os
import base64
import xml.etree.ElementTree as ET
from html import escape
import tempfile
import webbrowser

try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    print("pywebview not available, falling back to browser mode")
    WEBVIEW_AVAILABLE = False

def parse_object_xml(xml_path):
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

def extract_image_from_element(element):
    """Extract base64 image from element if present"""
    image_elem = element.find('.//image[@type="PNG"]')
    if image_elem is not None and image_elem.text:
        return image_elem.text.strip()
    return None

def get_element_properties(element):
    """Extract properties from element"""
    properties = {}
    
    # Direct attributes
    for key, value in element.attrib.items():
        properties[key] = value
    
    # Child elements that look like properties
    for child in element:
        if child.tag and child.text:
            properties[child.tag] = child.text.strip()
    
    return properties

def build_object_tree_html(element, level=0, path="0"):
    """Build HTML for object tree with proper click handling"""
    if element is None:
        return ""
    
    indent = "  " * level
    
    # Get basic info
    tag_name = element.tag or "unknown"
    
    # Get identifying attributes
    obj_name = element.get('name', '')
    class_name = element.get('class', '')
    text_content = element.get('text', '')
    
    # Build display text
    display_parts = [tag_name]
    if obj_name:
        display_parts.append(f'name="{obj_name}"')
    if class_name:
        display_parts.append(f'class="{class_name}"')
    if text_content and len(text_content) < 50:
        display_parts.append(f'text="{text_content[:30]}..."' if len(text_content) > 30 else f'text="{text_content}"')
    
    display_text = " ".join(display_parts)
    
    # Get geometry for overlay
    x = element.get('x', '0')
    y = element.get('y', '0')
    width = element.get('width', '0')
    height = element.get('height', '0')
    
    # Create the tree node
    html = f'''{indent}<div class="tree-item" data-path="{path}" data-x="{x}" data-y="{y}" data-width="{width}" data-height="{height}">
{indent}  <span class="tree-node" onclick="selectElement('{path}', {x}, {y}, {width}, {height})">{escape(display_text)}</span>
'''
    
    # Add children
    if list(element):
        html += f"{indent}  <div class=\"tree-children\">\n"
        for i, child in enumerate(element):
            child_path = f"{path}.{i}"
            html += build_object_tree_html(child, level + 2, child_path)
        html += f"{indent}  </div>\n"
    
    html += f"{indent}</div>\n"
    return html

class SquishXMLViewerDesktop:
    def __init__(self):
        self.current_xml_path = None
        self.html_content = None
        self.window = None  # Store window reference
    
    def open_file_dialog(self):
        """Open file dialog to select XML file"""
        if WEBVIEW_AVAILABLE and self.window:
            try:
                result = self.window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=('XML files (*.xml)',)
                )
                if result and len(result) > 0:
                    file_path = result[0]
                    self.load_xml_file(file_path)
            except Exception as e:
                print(f"File dialog error: {e}")
        else:
            print("File dialog not available in browser mode. Please provide XML file as command line argument.")
    
    def close_file(self):
        """Close current file"""
        self.current_xml_path = None
        self.html_content = None
        if WEBVIEW_AVAILABLE and self.window:
            initial_html = self.get_welcome_html()
            self.window.load_html(initial_html)
        else:
            print("File closed.")
    
    def show_about(self):
        """Show about dialog"""
        if WEBVIEW_AVAILABLE and self.window:
            self.window.evaluate_js('''
                alert("Squish XML Viewer Desktop\\n\\nA desktop application for viewing and analyzing Squish XML snapshot files.\\n\\nFeatures:\\n- Interactive object tree navigation\\n- Property inspection\\n- Screenshot visualization with element overlay\\n- Click-to-highlight functionality\\n\\nBuilt with Python and pywebview.");
            ''')
        else:
            print("About: Squish XML Viewer Desktop")
    
    def exit_app(self):
        """Exit application"""
        if WEBVIEW_AVAILABLE and self.window:
            self.window.destroy()
        else:
            sys.exit(0)
    
    def load_xml_file(self, xml_path):
        """Load XML file and generate HTML"""
        try:
            self.current_xml_path = xml_path
            
            # Parse XML
            root = parse_object_xml(xml_path)
            if root is None:
                self.show_error("Failed to parse XML file")
                return
            
            # Extract image
            image_base64 = extract_image_from_element(root)
            
            # Generate HTML
            self.html_content = self.generate_html(root, image_base64, xml_path)
            
            if WEBVIEW_AVAILABLE and self.window:
                self.window.load_html(self.html_content)
            else:
                # Save to temp file and open in browser
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(self.html_content)
                    temp_path = f.name
                
                webbrowser.open('file://' + temp_path)
                print(f"Opened in browser: {temp_path}")
                
        except Exception as e:
            self.show_error(f"Error loading XML file: {str(e)}")
    
    def show_error(self, message):
        """Show error message"""
        if WEBVIEW_AVAILABLE and self.window:
            self.window.evaluate_js(f'alert("Error: {escape(message)}");')
        else:
            print(f"Error: {message}")
    
    def get_welcome_html(self):
        """Generate welcome screen HTML with simple menu"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Squish XML Viewer Desktop</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
                .menu-bar { background: #2c3e50; color: white; padding: 10px 20px; border-bottom: 1px solid #34495e; }
                .menu-bar h2 { margin: 0; display: inline-block; }
                .menu-actions { float: right; }
                .btn { background: #3498db; color: white; border: none; padding: 8px 15px; margin-left: 10px; border-radius: 3px; cursor: pointer; }
                .btn:hover { background: #2980b9; }
                .welcome { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: 40px auto; }
                .logo { font-size: 48px; margin-bottom: 20px; text-align: center; }
                h1 { color: #2c3e50; margin-bottom: 10px; text-align: center; }
                p { color: #7f8c8d; margin-bottom: 30px; text-align: center; }
                .instructions { text-align: left; background: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 30px; }
                .file-input { display: none; }
            </style>
        </head>
        <body>
            <div class="menu-bar">
                <h2>📁 Squish XML Viewer Desktop</h2>
                <div class="menu-actions">
                    <button class="btn" onclick="openFile()">Open XML File</button>
                    <button class="btn" onclick="showAbout()">About</button>
                </div>
                <div style="clear: both;"></div>
            </div>
            
            <div class="welcome">
                <div class="logo">📁</div>
                <h1>Squish XML Viewer Desktop</h1>
                <p>A desktop application for viewing and analyzing Squish XML snapshot files.</p>
                
                <div class="instructions">
                    <h3>How to use:</h3>
                    <ul>
                        <li>Click <strong>"Open XML File"</strong> above to load an XML file</li>
                        <li>Click on elements in the Object Tree to highlight them on the screenshot</li>
                        <li>View element properties in the Properties panel</li>
                        <li>Use the search functionality to find specific elements</li>
                    </ul>
                    
                    <h3>Features:</h3>
                    <ul>
                        <li>✅ Interactive object tree navigation</li>
                        <li>✅ Property inspection</li>
                        <li>✅ Screenshot visualization with element overlay</li>
                        <li>✅ Click-to-highlight functionality</li>
                        <li>✅ Search and filtering</li>
                    </ul>
                </div>
            </div>
            
            <input type="file" id="fileInput" class="file-input" accept=".xml" onchange="handleFileSelect(this)">
            
            <script>
                function openFile() {
                    document.getElementById('fileInput').click();
                }
                
                function handleFileSelect(input) {
                    if (input.files && input.files[0]) {
                        const file = input.files[0];
                        if (file.name.toLowerCase().endsWith('.xml')) {
                            // Call Python API to load the file
                            if (window.pywebview && window.pywebview.api) {
                                // For now, just show a message
                                alert('File selected: ' + file.name + '\\n\\nNote: Direct file loading from browser is limited.\\nPlease restart the application with the XML file as argument:\\n\\npython squish_xml_viewer_desktop_simple.py "' + file.name + '"');
                            }
                        } else {
                            alert('Please select an XML file.');
                        }
                    }
                }
                
                function showAbout() {
                    alert('Squish XML Viewer Desktop v1.0\\n\\nA desktop application for viewing and analyzing Squish XML snapshot files.\\n\\nFeatures:\\n- Interactive object tree navigation\\n- Property inspection\\n- Screenshot visualization with element overlay\\n- Click-to-highlight functionality\\n- Search and filtering\\n\\nBuilt with Python and pywebview.');
                }
            </script>
        </body>
        </html>
        '''
    
    def generate_html(self, root, image_base64, xml_path):
        """Generate the complete HTML for the XML viewer"""
        
        # Build object tree
        tree_html = build_object_tree_html(root)
        
        # Get root properties
        root_properties = get_element_properties(root)
        properties_html = ""
        for key, value in root_properties.items():
            properties_html += f"<tr><td><strong>{escape(key)}</strong></td><td>{escape(str(value))}</td></tr>"
        
        # Prepare image
        image_html = ""
        if image_base64:
            image_html = f'<img id="screenshot" src="data:image/png;base64,{image_base64}" style="max-width: 100%; border: 1px solid #ddd; position: relative;" />'
        else:
            image_html = '<div style="padding: 40px; text-align: center; border: 2px dashed #ddd; color: #999;">No screenshot available</div>'
        
        html_template = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Squish XML Viewer - {os.path.basename(xml_path)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 10px 20px;
            border-bottom: 1px solid #34495e;
        }}
        .container {{
            display: flex;
            height: calc(100vh - 60px);
        }}
        .tree-panel {{
            width: 300px;
            background: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
            padding: 10px;
        }}
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .image-container {{
            flex: 1;
            padding: 20px;
            background: white;
            margin: 10px;
            border-radius: 5px;
            position: relative;
            overflow: auto;
        }}
        .properties-panel {{
            height: 200px;
            background: white;
            border-top: 1px solid #ddd;
            padding: 10px;
            overflow-y: auto;
            margin: 0 10px 10px 10px;
            border-radius: 5px;
        }}
        .tree-item {{
            margin-left: 15px;
        }}
        .tree-node {{
            cursor: pointer;
            padding: 2px 5px;
            border-radius: 3px;
            display: inline-block;
            margin: 1px 0;
            max-width: 250px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .tree-node:hover {{
            background: #e8f4fd;
        }}
        .tree-node.selected {{
            background: #3498db;
            color: white;
        }}
        .tree-children {{
            margin-left: 10px;
        }}
        .search-box {{
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }}
        .properties-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .properties-table th, .properties-table td {{
            padding: 5px 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .properties-table th {{
            background: #f8f9fa;
            font-weight: bold;
        }}
        .element-overlay {{
            position: absolute;
            border: 2px solid red;
            background: rgba(255, 0, 0, 0.1);
            pointer-events: none;
            z-index: 1000;
        }}
        .status-bar {{
            background: #34495e;
            color: white;
            padding: 5px 20px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0;">📁 {escape(os.path.basename(xml_path))}</h2>
    </div>
    
    <div class="container">
        <div class="tree-panel">
            <input type="text" id="searchBox" class="search-box" placeholder="Search elements..." onkeyup="searchTree()">
            <h3>Object Tree</h3>
            <div id="tree">
                {tree_html}
            </div>
        </div>
        
        <div class="main-content">
            <div class="image-container" id="imageContainer">
                {image_html}
            </div>
            
            <div class="properties-panel">
                <h3>Properties</h3>
                <table class="properties-table" id="propertiesTable">
                    <tbody>
                        {properties_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <div class="status-bar">
        <span id="statusText">Ready - Click on elements in the tree to highlight them on the screenshot</span>
    </div>

    <script>
        let selectedElement = null;
        let allElements = [];
        
        // Collect all elements for search
        function collectElements() {{
            allElements = [];
            document.querySelectorAll('[data-path]').forEach(elem => {{
                allElements.push({{
                    element: elem,
                    text: elem.textContent.toLowerCase(),
                    path: elem.getAttribute('data-path')
                }});
            }});
        }}
        
        // Search functionality
        function searchTree() {{
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            allElements.forEach(item => {{
                if (searchTerm === '' || item.text.includes(searchTerm)) {{
                    item.element.style.display = 'block';
                }} else {{
                    item.element.style.display = 'none';
                }}
            }});
        }}
        
        // Element selection and overlay
        function selectElement(path, x, y, width, height) {{
            // Remove previous selection
            if (selectedElement) {{
                selectedElement.classList.remove('selected');
            }}
            
            // Select new element
            selectedElement = document.querySelector(`[data-path="${{path}}"]`).querySelector('.tree-node');
            selectedElement.classList.add('selected');
            
            // Update properties
            updateElementProperties(path);
            
            // Update overlay
            updateElementOverlay(parseInt(x), parseInt(y), parseInt(width), parseInt(height));
            
            // Update status
            document.getElementById('statusText').textContent = `Selected element at (${{x}},${{y}}, ${{width}}x${{height}})`;
        }}
        
        function updateElementProperties(path) {{
            const element = document.querySelector(`[data-path="${{path}}"]`);
            const table = document.getElementById('propertiesTable').querySelector('tbody');
            table.innerHTML = '';
            
            if (element) {{
                // Add basic properties
                const properties = {{
                    'path': path,
                    'x': element.getAttribute('data-x'),
                    'y': element.getAttribute('data-y'),
                    'width': element.getAttribute('data-width'),
                    'height': element.getAttribute('data-height')
                }};
                
                for (const [key, value] of Object.entries(properties)) {{
                    if (value) {{
                        const row = table.insertRow();
                        row.innerHTML = `<td><strong>${{key}}</strong></td><td>${{value}}</td>`;
                    }}
                }}
            }}
        }}
        
        function updateElementOverlay(x, y, width, height) {{
            // Remove existing overlay
            const existingOverlay = document.querySelector('.element-overlay');
            if (existingOverlay) {{
                existingOverlay.remove();
            }}
            
            // Create new overlay if we have valid coordinates
            if (x >= 0 && y >= 0 && width > 0 && height > 0) {{
                const screenshot = document.getElementById('screenshot');
                if (screenshot) {{
                    const overlay = document.createElement('div');
                    overlay.className = 'element-overlay';
                    overlay.style.left = x + 'px';
                    overlay.style.top = y + 'px';
                    overlay.style.width = width + 'px';
                    overlay.style.height = height + 'px';
                    
                    screenshot.parentElement.appendChild(overlay);
                }}
            }}
        }}
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            collectElements();
        }});
    </script>
</body>
</html>
        '''
        
        return html_template
    
    def run(self, xml_path=None):
        """Run the desktop application"""
        if WEBVIEW_AVAILABLE:
            # Create initial HTML
            if xml_path and os.path.exists(xml_path):
                self.load_xml_file(xml_path)
                initial_html = self.html_content
            else:
                initial_html = self.get_welcome_html()
            
            # Create webview window without problematic menu
            self.window = webview.create_window(
                'Squish XML Viewer',
                html=initial_html,
                width=1400,
                height=900,
                min_size=(800, 600),
                js_api=self
            )
            
            # Start the application
            webview.start(debug=False)
        else:
            # Fallback to browser mode
            if xml_path and os.path.exists(xml_path):
                self.load_xml_file(xml_path)
            else:
                print("Please provide an XML file path as argument")
                print("Usage: python3 squish_xml_viewer_desktop_simple.py path/to/file.xml")

def main():
    """Main function"""
    app = SquishXMLViewerDesktop()
    
    # Check command line arguments
    xml_path = None
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
        if not os.path.exists(xml_path):
            print(f"Error: File '{xml_path}' not found")
            sys.exit(1)
    
    app.run(xml_path)

if __name__ == "__main__":
    main()