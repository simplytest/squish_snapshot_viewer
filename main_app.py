import webview
import sys
import os
import base64
import xml.etree.ElementTree as ET
from html import escape
from webview.menu import Menu, MenuAction
import json

# This code is adapted from squish_xml_viewer_templated.py to avoid changing it.

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
    """Load asset file content"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, file_name)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Asset file not found: {file_path}")

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
    html = html.replace('{SCREENSHOT_NAME}', "Screenshot")
    html = html.replace('{RAW_XML}', escape(raw_xml))

    return html

def main():
    LAST_FILE_CONFIG = '.last_opened_file'
    
    window = webview.create_window(
        'Squish Snapshot Viewer',
        html="<html><body><h1>loading...</h1></body></html>",
        width=1200,
        height=800
    )

    def load_initial_file():
        initial_html = "<h1>Squish Snapshot Viewer</h1><p>Use the File > Open menu to select an XML file to view.</p>"
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            initial_html = generate_html_from_xml(sys.argv[1])
            with open(LAST_FILE_CONFIG, 'w') as f:
                f.write(sys.argv[1])
        else:
            try:
                with open(LAST_FILE_CONFIG, 'r') as f:
                    last_file = f.read().strip()
                    if os.path.isfile(last_file):
                        initial_html = generate_html_from_xml(last_file)
            except FileNotFoundError:
                pass # No last file saved, show welcome screen
        window.load_html(initial_html)

    def open_file():
        file_types = ["XML files (*.xml)", "All files (*.*)"]
        result = window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False, file_types=file_types)
        if result:
            xml_file = result[0]
            html_content = generate_html_from_xml(xml_file)
            window.load_html(html_content)
            with open(LAST_FILE_CONFIG, 'w') as f:
                f.write(xml_file)

    def exit_app():
        window.destroy()

    def show_about_window():
        class Api:
            def close_window(self):
                about_window.destroy()

        try:
            about_html = load_asset('about.html')
            api = Api()
            about_window = webview.create_window('About', html=about_html, width=400, height=400, frameless=True, js_api=api)
        except FileNotFoundError as e:
            webview.create_window('Error', html=f'<h1>{e}</h1>', width=400, height=200)

    menu_items = [
        Menu('File', [
            MenuAction('Open', open_file),
            MenuAction('Exit', exit_app)
        ]),
        Menu('Help', [
            MenuAction('About', show_about_window)
        ])
    ]

    webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
    webview.start(menu=menu_items, func=load_initial_file, debug=True)

if __name__ == '__main__':
    main()
