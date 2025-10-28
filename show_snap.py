import sys
import os
import xml.etree.ElementTree as ET
from html import escape
import json
import webbrowser

# ANSI escape codes for colors
COLOR_RED = '\033[91m'
COLOR_GREEN = '\033[92m'
COLOR_YELLOW = '\033[93m'
COLOR_BLUE = '\033[94m'
COLOR_RESET = '\033[0m'

CONFIG_FILE = ".last_folder"
SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

def parse_object_xml(xml_path):
    """Parse XML file and return root element"""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        xml_start = content.find('<ui')
        if xml_start == -1:
            xml_start = content.find('<')
        
        if xml_start > 0:
            content = content[xml_start:]
        
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

def build_tree_html(node, counter=None):
    """Build HTML tree structure from XML node"""
    if counter is None:
        counter = {"i": 1}
    myid = counter["i"]
    counter["i"] += 1

    simplified_type = node.attrib.get("simplifiedType", "")
    object_name_attr = node.attrib.get("objectName", "") # Renamed to avoid conflict
    class_name = node.attrib.get("class", "")
    
    # --- START OF MOVED BLOCK (properties dictionary construction) ---
    properties = {}
    properties.update(node.attrib)
    
    realname_elem = node.find("realname")
    if realname_elem is not None and realname_elem.text:
        properties["realname"] = realname_elem.text.strip()
    
    superclass_elem = node.find("superclass")
    if superclass_elem is not None:
        classes = [cls.text for cls in superclass_elem.findall("class") if cls.text]
        if classes:
            properties["superclasses"] = " > ".join(classes)
    
    geom_elem = node.find("abstractProperties/geometry")
    if geom_elem is not None:
        for coord in ["x", "y", "width", "height"]:
            coord_elem = geom_elem.find(coord)
            if coord_elem is not None and coord_elem.text:
                properties[f"geometry_{coord}"] = coord_elem.text
    
    visual_elem = node.find("abstractProperties/visual")
    if visual_elem is not None:
        for attr_name, attr_value in visual_elem.attrib.items():
            properties[f"visual_{attr_name}"] = attr_value
    
    props_elem = node.find("properties")
    if props_elem is not None:
        for prop in props_elem.findall("property"):
            prop_name = prop.attrib.get("name", "")
            prop_value = ""
            if prop.find("string") is not None:
                prop_value = prop.find("string").text or ""
            properties[prop_name] = prop_value
    # --- END OF MOVED BLOCK ---

    label_base = ""
    # 1. Try objectName from node.attrib
    if object_name_attr: # Use the renamed variable
        label_base = object_name_attr
    else:
        # 2. If not found, check for a property named "objectName"
        property_object_name = properties.get("objectName", "")
        if property_object_name:
            label_base = property_object_name
        # 3. If still not found, use simplified_type from node.attrib
        elif simplified_type:
            label_base = simplified_type
        # 4. Fallback to XML tag
        else:
            label_base = node.tag

    # Remove class_name from label as per user request to shorten names
    label = label_base
    
    data_props = escape(json.dumps(properties)).replace('"', '&quot;')
    xml_snippet = ET.tostring(node, encoding='unicode')
    data_xml = escape(xml_snippet).replace('"', '&quot;')
    
    html_parts = [] # Initialize as empty list
    
    children = []
    children_elem = node.find("children")
    if children_elem is not None:
        children = children_elem.findall("element")
    else:
        children = [child for child in node if child.tag == "element"]
    
    if children:
        # Add a toggle span if there are children
        html_parts.append(f'''<li><span class="toggle">-</span><span class="node" data-id="{myid}" data-props="{data_props}" data-xml="{data_xml}">{escape(label)}</span>''')
        html_parts.append("<ul class='nested'>") # Add 'nested' class
        for child in children:
            frag = build_tree_html(child, counter)[0]
            html_parts.append(frag)
        html_parts.append("</ul>")
    else:
        html_parts.append(f'''<li><span class="node" data-id="{myid}" data-props="{data_props}" data-xml="{data_xml}">{escape(label)}</span>''')
    html_parts.append("</li>")
    return ("\n".join(html_parts), counter["i"])

def load_asset(file_name):
    """Load asset file content from the filesystem."""
    asset_path = os.path.join(SCRIPT_DIR, file_name)
    try:
        with open(asset_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Asset file not found: {asset_path}")

def load_whitelist(file_name='whitelist.txt'):
    """Load whitelist from a file."""
    asset_path = os.path.join(SCRIPT_DIR, file_name)
    try:
        with open(asset_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def generate_html_from_xml(xml_path):
    """Generate HTML viewer content from an XML file"""
    xml_root = parse_object_xml(xml_path)
    if xml_root is None:
        return "<h1>Error: Failed to parse XML file.</h1>"

    screenshot_b64 = ""
    first_element = xml_root.find(".//element")
    if first_element is not None:
        image_data = extract_image_from_element(first_element)
        if image_data:
            screenshot_b64 = image_data

    tree_html = "<p><i>No object structure found.</i></p>"
    root_element = xml_root.find(".//element")
    if root_element is not None:
        tree_html_frag = build_tree_html(root_element)[0]
        tree_html = f"<ul class='tree'>\n{tree_html_frag}\n</ul>"
    
    with open(xml_path, "r", encoding="utf-8", errors="replace") as fh:
        raw_xml = fh.read()

    title = escape(os.path.basename(xml_path))
    if screenshot_b64:
        screenshot_img = f"<img class='screenshot' src='data:image/png;base64,{screenshot_b64}'>"
    else:
        screenshot_img = "<p><i>No screenshot found.</i></p>"

    try:
        html_template = load_asset('viewer_template.html')
        css_content = load_asset('viewer_styles.css')
        js_content = load_asset('viewer_scripts.js')
    except FileNotFoundError as e:
        return f"<h1>Error: {e}</h1>"

    whitelist = load_whitelist()
    html_template = html_template.replace('{WHITELIST}', json.dumps(whitelist))

    html_template = html_template.replace('<link rel="stylesheet" href="viewer_styles.css">', f'<style>{css_content}</style>')
    html_template = html_template.replace('<script src="viewer_scripts.js"></script>', f'<script>{js_content}</script>')

    html = html_template.replace('{TITLE}', title)
    html = html.replace('{TREE_HTML}', tree_html)
    html = html.replace('{SCREENSHOT_IMG}', screenshot_img)
    html = html.replace('{SCREENSHOT_NAME}', f"Screenshot for {os.path.splitext(os.path.basename(xml_path))[0]}")
    html = html.replace('{RAW_XML}', escape(raw_xml))
    html = html.replace('{XML_FILE_PATH}', os.path.abspath(xml_path))

    return html

def select_xml_file(path):
    """
    Handles the selection of an XML file from a given path.
    Returns the absolute path to the selected XML file, or "EXIT_PROGRAM"
    if no XML files are found.
    """
    xml_files = [f for f in os.listdir(path) if f.endswith('.xml')]
    if not xml_files:
        print(f"{COLOR_RED}No XML files found in '{path}'{COLOR_RESET}")
        return "EXIT_PROGRAM"

    if len(xml_files) == 1:
        print(f"{COLOR_BLUE}Automatically selecting the only XML file: {xml_files[0]}{COLOR_RESET}")
        return os.path.join(path, xml_files[0])

    # Non-interactive: just select the first one.
    print(f"{COLOR_BLUE}Multiple XML files found. Automatically selecting the first one: {xml_files[0]}{COLOR_RESET}")
    return os.path.join(path, xml_files[0])

def show_help():
    """Prints the help message."""
    print("Usage: python show_snap.py [path]")
    print("  [path] can be a path to an XML file or a directory containing XML files.")
    print("If no path is provided, it will try to load the last used directory.")

def load_last_folder_path():
    """Loads the last used folder path from the config file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_folder_path(path):
    """Saves the last used folder path to the config file."""
    with open(CONFIG_FILE, "w") as f:
        f.write(path)

def main():
    """
    CLI to generate and view a Squish snapshot report.
    """
    input_path = None
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = load_last_folder_path()

    if not input_path:
        show_help()
        return

    current_path = input_path
    while True:
        xml_path = None
        
        if os.path.isfile(current_path) and current_path.endswith('.xml'):
            xml_path = current_path
            current_path = os.path.dirname(current_path)
            save_last_folder_path(current_path)
            print(f"{COLOR_BLUE}Processing specified XML file: {xml_path}...{COLOR_RESET}")
        elif os.path.isdir(current_path):
            save_last_folder_path(current_path)
            print(f"{COLOR_BLUE}Searching directory '{current_path}' for XML files.{COLOR_RESET}")
            selected = select_xml_file(current_path)
            if selected == "EXIT_PROGRAM":
                break
            xml_path = selected
        else:
            print(f"{COLOR_RED}Error: '{current_path}' is not a valid XML file or a directory.{COLOR_RESET}\n")
            break

        if xml_path:
            html_content = generate_html_from_xml(xml_path)
            base_name = os.path.splitext(os.path.basename(xml_path))[0]
            report_filename = f"{base_name}_view.html"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"{COLOR_GREEN}Report saved to {report_filename}{COLOR_RESET}")
            webbrowser.open(f'file://{os.path.realpath(report_filename)}')
            print(f"{COLOR_BLUE}Opening report in your default web browser...{COLOR_RESET}")

        print(f"{COLOR_YELLOW}Press 'x' or '0' to exit, or any other key to select another file from the same directory:{COLOR_RESET}")
        choice = input("> ").strip().lower()
        if choice in ('x', '0'):
            break

if __name__ == '__main__':
    main()
