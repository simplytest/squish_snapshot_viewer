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

# This code is adapted from main_app.py

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
    object_name = node.attrib.get("objectName", "")
    class_name = node.attrib.get("class", "")
    
    if simplified_type:
        label = f"{simplified_type} ({object_name})" if object_name else simplified_type
    else:
        label = node.tag
        if object_name:
            label = f"{label} ({object_name})"
        elif class_name:
            label = f"{label} ({class_name})"
    
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
    
    data_props = escape(json.dumps(properties)).replace('"', '&quot;')
    xml_snippet = ET.tostring(node, encoding='unicode')
    data_xml = escape(xml_snippet).replace('"', '&quot;')
    
    html_parts = [f'''<li><span class="node" data-id="{myid}" data-props="{data_props}" data-xml="{data_xml}">{escape(label)}</span>''']
    
    children = []
    children_elem = node.find("children")
    if children_elem is not None:
        children = children_elem.findall("element")
    else:
        children = [child for child in node if child.tag == "element"]
    
    if children:
        html_parts.append("<ul>")
        for child in children:
            frag = build_tree_html(child, counter)[0]
            html_parts.append(frag)
        html_parts.append("</ul>")
    html_parts.append("</li>")
    return ("\n".join(html_parts), counter["i"])

def load_asset(file_name):
    """Load asset file content from the filesystem."""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Asset file not found: {file_name}")

def load_whitelist(file_name='whitelist.txt'):
    """Load whitelist from a file."""
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
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

    return html

def select_xml_file(path):
    """
    Handles the interactive selection of an XML file from a given path.
    Returns the absolute path to the selected XML file, "EXIT_PROGRAM" if the user
    chooses to exit, or None if no XML files are found or an error occurs.
    """
    xml_files = [f for f in os.listdir(path) if f.endswith('.xml')]
    if not xml_files:
        print(f"{COLOR_RED}No XML files found in '{path}'{COLOR_RESET}")
        return "EXIT_PROGRAM" # Indicate no file found, but don't exit program

    if len(xml_files) == 1:
        print(f"{COLOR_BLUE}Automatically selecting the only XML file: {xml_files[0]}{COLOR_RESET}")
        return os.path.join(path, xml_files[0])

    page_size = 10
    current_page = 0
    while True:
        start_index = current_page * page_size
        end_index = min(start_index + page_size, len(xml_files))

        print(f"{COLOR_YELLOW}--- Page {current_page + 1}/{(len(xml_files) + page_size - 1) // page_size} ---")
        for i in range(start_index, end_index):
            print(f"  {COLOR_GREEN}{i+1}:{COLOR_RESET} {xml_files[i]}")

        print(f"{COLOR_YELLOW}Enter number (1-{len(xml_files)}), full filename, 'n' for next, 'p' for previous, or 'x'/'0' to exit:{COLOR_RESET}")

        try:
            choice = input("> ").strip().lower()

            if choice in ('x', '0'):
                print(f"{COLOR_BLUE}Aborted.{COLOR_RESET}")
                return "EXIT_PROGRAM" # Special value to indicate program exit
            elif choice == 'n':
                if end_index < len(xml_files):
                    current_page += 1
                else:
                    print(f"{COLOR_YELLOW}No next page.{COLOR_RESET}")
            elif choice == 'p':
                if current_page > 0:
                    current_page -= 1
                else:
                    print(f"{COLOR_YELLOW}No previous page.{COLOR_RESET}")
            elif choice.isdigit():
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(xml_files):
                    selected_file = xml_files[choice_index]
                    return os.path.join(path, selected_file)
                else:
                    print(f"{COLOR_RED}Invalid number, please try again.{COLOR_RESET}")
            elif choice in xml_files:
                selected_file = choice
                return os.path.join(path, selected_file)
            else:
                print(f"{COLOR_RED}Invalid input, please enter a number, a valid filename, 'n', 'p', 'x', or '0'.{COLOR_RESET}")
        except (KeyboardInterrupt, EOFError):
            print(f"{COLOR_BLUE}\nAborted.{COLOR_RESET}")
            return "EXIT_PROGRAM" # Indicate program exit

def main():
    """
    CLI to generate and view a Squish snapshot report.
    """
    first_run = True
    while True: # Main loop to keep the program running
        xml_path = None
        
        if first_run and len(sys.argv) > 1:
            input_path = sys.argv[1]
            if os.path.isfile(input_path) and input_path.endswith('.xml'):
                xml_path = input_path
                print(f"{COLOR_BLUE}Processing specified XML file: {xml_path}...{COLOR_RESET}")
            elif os.path.isdir(input_path):
                print(f"{COLOR_BLUE}Searching directory '{input_path}' for XML files.{COLOR_RESET}")
                selected = select_xml_file(input_path)
                if selected == "EXIT_PROGRAM":
                    break # Exit main loop
                xml_path = selected
            else:
                print(f"{COLOR_RED}Error: '{input_path}' is neither a valid XML file nor a directory.{COLOR_RESET}\n")
                # If initial input is invalid, we should continue the loop to prompt for selection.
                pass
        else: # Subsequent runs or no initial argument
            print(f"{COLOR_BLUE}No file or directory specified. Searching current directory for XML files.{COLOR_RESET}")
            selected = select_xml_file('.')
            if selected == "EXIT_PROGRAM":
                break # Exit main loop
            xml_path = selected

        first_run = False # Mark that the first run is over

        if xml_path: # Only generate report if a file was successfully selected
            html_content = generate_html_from_xml(xml_path)
            base_name = os.path.splitext(os.path.basename(xml_path))[0]
            report_filename = f"{base_name}_view.html"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"{COLOR_GREEN}Report saved to {report_filename}{COLOR_RESET}")
            webbrowser.open(f'file://{os.path.realpath(report_filename)}')
            print(f"{COLOR_BLUE}Opening report in your default web browser...{COLOR_RESET}")
        else:
            # If xml_path is None here, it means select_xml_file returned None (no files found) or the initial input was invalid.
            # We should continue the loop to prompt again.
            pass

        # After generating, ask if they want to continue or exit
        if xml_path: # Only prompt for exit if a report was generated
            print(f"{COLOR_YELLOW}Press 'x' or '0' to exit, or any other key to generate another report:{COLOR_RESET}")
            post_report_choice = input("> ").strip().lower()
            if post_report_choice in ('x', '0'):
                print(f"{COLOR_BLUE}Exiting program.{COLOR_RESET}")
                break # Exit the main loop

if __name__ == '__main__':
    main()