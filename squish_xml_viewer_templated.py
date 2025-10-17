#!/usr/bin/env python3
"""
squish_xml_viewer_templated.py

Templated version of the Squish XML Viewer.
Uses external HTML template and JavaScript files for better code organization.

Usage:
    python3 squish_xml_viewer_templated.py path/to/snapshot.xml

Output:
    <xml_basename>_viewer.html in the same directory as the XML file.
"""

import sys
import os
import base64
import xml.etree.ElementTree as ET
from html import escape

def parse_object_xml(xml_path):
    """Parse XML file and return root element"""
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

def build_tree_html(node, counter=None):
    """Build HTML tree structure from XML node"""
    if counter is None:
        counter = {"i": 1}
    myid = counter["i"]
    counter["i"] += 1

    # Build label from XML element, starting with simplifiedType if available
    simplified_type = node.attrib.get("simplifiedType", "")
    object_name = node.attrib.get("objectName", "")
    class_name = node.attrib.get("class", "")
    
    if simplified_type:
        if object_name:
            label = f"{simplified_type} ({object_name})"
        else:
            label = simplified_type
    else:
        # Fallback to original logic if no simplifiedType
        label = node.tag
        if object_name:
            label = f"{label} ({object_name})"
        elif class_name:
            label = f"{label} ({class_name})"
    
    # Collect all properties for this element
    properties = {}
    properties.update(node.attrib)  # Add XML attributes
    
    # Add realname if it exists
    realname_elem = node.find("realname")
    if realname_elem is not None and realname_elem.text:
        properties["realname"] = realname_elem.text.strip()
    
    # Add superclass information if it exists
    superclass_elem = node.find("superclass")
    if superclass_elem is not None:
        classes = [cls.text for cls in superclass_elem.findall("class") if cls.text]
        if classes:
            properties["superclasses"] = " > ".join(classes)
    
    # Add geometry information if it exists
    geom_elem = node.find("abstractProperties/geometry")
    if geom_elem is not None:
        for coord in ["x", "y", "width", "height"]:
            coord_elem = geom_elem.find(coord)
            if coord_elem is not None and coord_elem.text:
                properties[f"geometry_{coord}"] = coord_elem.text
    
    # Add visual properties if they exist
    visual_elem = node.find("abstractProperties/visual")
    if visual_elem is not None:
        for attr_name, attr_value in visual_elem.attrib.items():
            properties[f"visual_{attr_name}"] = attr_value
    
    # Add properties from properties subelement if it exists
    props_elem = node.find("properties")
    if props_elem is not None:
        for prop in props_elem.findall("property"):
            prop_name = prop.attrib.get("name", "")
            prop_value = ""
            if prop.find("string") is not None:
                prop_value = prop.find("string").text or ""
            properties[prop_name] = prop_value
    
    data_props = escape(str(properties)).replace('"', '&quot;')
    xml_snippet = ET.tostring(node, encoding='unicode')
    data_xml = escape(xml_snippet).replace('"', '&quot;')
    
    html_parts = []
    html_parts.append(f'<li><span class="node" data-id="{myid}" data-props="{data_props}" data-xml="{data_xml}">{escape(label)}</span>')
    
    # Process children (look for 'children' element or direct child elements)
    children = []
    children_elem = node.find("children")
    if children_elem is not None:
        children = children_elem.findall("element")
    else:
        # Look for direct element children
        children = [child for child in node if child.tag == "element"]
    
    if children:
        html_parts.append("<ul>")
        for child in children:
            frag = build_tree_html(child, counter)[0]
            html_parts.append(frag)
        html_parts.append("</ul>")
    html_parts.append("</li>")
    return ("\n".join(html_parts), counter["i"])

def load_template(template_path):
    """Load HTML template from file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_file = os.path.join(script_dir, template_path)
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file not found: {template_file}")

def load_css():
    """Load CSS content from external file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    css_file = os.path.join(script_dir, 'viewer_styles.css')
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"CSS file not found: {css_file}")

def load_javascript():
    """Load JavaScript content from external file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    js_file = os.path.join(script_dir, 'viewer_scripts.js')
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"JavaScript file not found: {js_file}")

def generate_html(xml_path, html_path):
    """Generate HTML viewer from XML file using templates"""
    xml_root = parse_object_xml(xml_path)
    if xml_root is None:
        print("Failed to parse XML file")
        return

    # Try to extract screenshot from first element with image
    screenshot_b64 = ""
    screenshot_name = ""
    
    # Look for image in the root or first element
    first_element = xml_root.find(".//element")
    if first_element is not None:
        image_data = extract_image_from_element(first_element)
        if image_data:
            screenshot_b64 = image_data
            screenshot_name = "Screenshot from XML"

    tree_html = "<p><i>No object structure found in XML.</i></p>"
    if xml_root is not None:
        # Try to build tree from the root or from elements
        if xml_root.find(".//element") is not None:
            # Find the root element to start from
            root_element = xml_root.find(".//element")
            tree_html_frag = build_tree_html(root_element)[0]
            tree_html = "<ul class='tree'>\n" + tree_html_frag + "\n</ul>"
        else:
            # Try to use the XML root directly
            tree_html_frag = build_tree_html(xml_root)[0]
            tree_html = "<ul class='tree'>\n" + tree_html_frag + "\n</ul>"

    # Get raw XML content
    with open(xml_path, "r", encoding="utf-8", errors="replace") as fh:
        raw_xml = fh.read()

    title = escape(os.path.basename(xml_path))
    
    # Build screenshot image HTML
    screenshot_img = f"<img class='screenshot' src='data:image/png;base64,{screenshot_b64}'> " if screenshot_b64 else "<p><i>No screenshot found.</i></p>"
    
    # Load HTML template
    try:
        html_template = load_template('viewer_template.html')
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure viewer_template.html is in the same directory as this script.")
        return
    
    # Load CSS content
    try:
        css_content = load_css()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure viewer_styles.css is in the same directory as this script.")
        return
    
    # Load JavaScript content
    try:
        js_content = load_javascript()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure viewer_scripts.js is in the same directory as this script.")
        return
    
    # Replace CSS and JavaScript links with inline content
    html_template = html_template.replace('<link rel="stylesheet" href="viewer_styles.css">', f'<style>\n{css_content}\n</style>')
    html_template = html_template.replace('<script src="viewer_scripts.js"></script>', f'<script>\n{js_content}\n</script>')
    
    # Replace template placeholders
    html = html_template.replace('{TITLE}', title)
    html = html.replace('{TREE_HTML}', tree_html)
    html = html.replace('{SCREENSHOT_IMG}', screenshot_img)
    html = html.replace('{SCREENSHOT_NAME}', escape(screenshot_name))
    html = html.replace('{RAW_XML}', escape(raw_xml))
    
    # Write the final HTML file
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Generated HTML viewer: {html_path}")
    print(f"Templates used:")
    print(f"  - HTML: viewer_template.html")
    print(f"  - CSS: viewer_styles.css")
    print(f"  - JavaScript: viewer_scripts.js")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 squish_xml_viewer_templated.py path/to/file.xml")
        sys.exit(1)
    xml_path = sys.argv[1]
    if not os.path.isfile(xml_path):
        print("XML file not found:", xml_path)
        sys.exit(2)
    out_html = os.path.splitext(xml_path)[0] + "_viewer.html"
    try:
        generate_html(xml_path, out_html)
    except Exception as e:
        print("Error generating viewer:", e)
        sys.exit(3)

if __name__ == "__main__":
    main()