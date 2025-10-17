#!/usr/bin/env python3
"""
squish_xml_viewer_desktop.py

Desktop version of the Squish XML Viewer using pywebview.
Creates a native desktop application for viewing XML snapshots.

Requirements:
    pip install pywebview

Usage:
    python3 squish_xml_viewer_desktop.py [path/to/snapshot.xml]

Features:
    - Native desktop window
    - Same UI and functionality as web version
    - Click-to-highlight overlay functionality
"""

import sys
import os
import base64
import xml.etree.ElementTree as ET
from html import escape

# Try to import webview, fall back to browser if not available
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("Warning: pywebview not installed. Falling back to browser mode.")
    print("Install with: pip install pywebview")

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

def build_tree_html(node, counter=None):
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

def generate_html(xml_path, html_path):
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
    
    # Build the HTML string separately to avoid f-string issues with JavaScript
    screenshot_img = f"<img class='screenshot' src='data:image/png;base64,{screenshot_b64}'> " if screenshot_b64 else "<p><i>No screenshot found.</i></p>"
    
    # Use template string replacement to avoid JavaScript curly brace issues
    html_template = '''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>XML Viewer - {TITLE}</title>
<style>
body{{font-family: Arial, Helvetica, sans-serif; margin:0; padding:0;}}
.header{{padding:10px; background:#2c3e50; color:white; display:flex; align-items:center; gap:15px;}}
.header h1{{margin:0; font-size:18px; color:white;}}
.header-search-group{{display:flex; align-items:center; gap:10px;}}
.header-search-group label{{font-size:12px; color:#ecf0f1; white-space:nowrap;}}
.header-search-group input, .header-search-group select{{padding:4px; border:none; border-radius:3px; font-size:12px;}}
.header-search-group .search-container{{position:relative;}}
.header .clear-btn{{color:#666; background:white;}}
.container{{display:flex; height:calc(100vh - 70px);}}
.sidebar{{width:360px; border-right:1px solid #ddd; display:flex; flex-direction:column;}}
.sidebar-header{{padding:10px; border-bottom:1px solid #eee; background:#f9f9f9;}}
.sidebar-content{{flex:1; padding:10px; overflow:auto;}}
.right-panel{{flex:1; display:flex; flex-direction:column;}}
.screenshot-panel{{height:320px; padding:10px; border-bottom:1px solid #ddd; overflow:hidden; flex-shrink:0;}}
.properties-panel{{flex:1; display:flex; flex-direction:column; min-height:0;}}
.properties-header{{padding:10px; border-bottom:1px solid #eee; background:#f9f9f9; flex-shrink:0;}}
.properties-content{{flex:1; padding:10px; overflow:auto; min-height:0;}}
.tree {{ list-style:none; padding-left:20px; }}
.tree li {{ margin:2px 0; }}
.node {{ cursor:pointer; display:inline-block; padding:2px 6px; border-radius:4px; }}
.node:hover {{ background:#eef; }}
.node.selected {{ background:#d0e7ff; }}
.props {{ white-space:pre-wrap; font-family: monospace; background:#f7f7f7; padding:8px; border-radius:4px; max-height:300px; overflow:auto; }}
.props-table {{ width:100%; border-collapse:collapse; font-size:12px; }}
.props-table th, .props-table td {{ border:1px solid #ddd; padding:4px 8px; text-align:left; }}
.props-table th {{ background:#f0f0f0; font-weight:bold; }}
.props-table tr:nth-child(even) {{ background:#f9f9f9; }}
.props-table td:first-child {{ font-weight:bold; color:#666; max-width:150px; word-break:break-word; }}
.props-table td:last-child {{ font-family:monospace; max-width:200px; word-break:break-all; }}
.props-table .group-header {{ background:#e8f4fd; }}
.props-table .group-header td {{ font-weight:bold; color:#2c3e50; border-bottom:2px solid #3498db; }}
.props-table .group-item {{ background:#f8fcff; }}
.props-table .group-item td:first-child {{ padding-left:20px; font-style:italic; color:#34495e; }}
.props-table tr:hover {{ background:#f0f8ff; cursor:pointer; }}
.props-table tr.selected {{ background:#d4edda; }}
.props-table tr.selected td {{ background:transparent; }}
.context-menu {{ position:absolute; background:white; border:1px solid #ccc; border-radius:4px; padding:5px 0; box-shadow:2px 2px 10px rgba(0,0,0,0.3); z-index:1000; display:none; }}
.context-menu-item {{ padding:5px 15px; cursor:pointer; }}
.context-menu-item:hover {{ background:#f0f0f0; }}
.node {{ position:relative; }}
.props-table td {{ position:relative; }}
.search-container {{ position:relative; width:100%; }}
.search-container input {{ width:100%; box-sizing:border-box; }}
.clear-btn {{ position:absolute; right:5px; top:50%; transform:translateY(-50%); background:none; border:none; font-size:16px; cursor:pointer; color:#666; padding:0; width:20px; height:20px; display:none; }}
.clear-btn:hover {{ color:#333; background:#f0f0f0; border-radius:50%; }}
.search-container input:not(:placeholder-shown) + .clear-btn {{ display:block; }}
.screenshot {{ max-width:100%; max-height:280px; border:1px solid #ccc; object-fit:contain; }}
.screenshot-panel .panel {{ height:280px; overflow:auto; }}
.screenshot-container {{ position:relative; display:inline-block; max-width:100%; }}
.element-overlay {{ position:absolute; border:2px solid red; background:rgba(255,0,0,0.1); pointer-events:none; z-index:10; }}
.screenshot-panel {{ position:relative; }}



</style>
</head>
<body>
<div class="header">
  <h1>Object Viewer</h1>
  <div class="header-search-group">
    <label>Tree:</label>
    <div class="search-container">
      <input id="treeSearch" placeholder="Search tree..." style="width:150px; padding:4px; padding-right:25px;">
      <button id="clearTreeSearch" class="clear-btn" onclick="clearTreeSearch()" title="Clear search">&times;</button>
    </div>
  </div>
  <div class="header-search-group">
    <label>Properties:</label>
    <div class="search-container">
      <input id="propsSearch" placeholder="Search properties..." style="width:150px; padding:4px; padding-right:25px;">
      <button id="clearPropsSearch" class="clear-btn" onclick="clearPropsSearch()" title="Clear search">&times;</button>
    </div>
  </div>
  <div class="header-search-group">
    <label>Sort:</label>
    <select id="sortOrder" onchange="refreshProperties()" style="padding:4px;">
      <option value="desc">Descending</option>
      <option value="asc">Ascending</option>
      <option value="none">None</option>
    </select>
  </div>
</div>
<div class="container">
  <div class="sidebar">
    <div class="sidebar-header">
      <h3 style="margin:0;">Object Tree</h3>
    </div>
    <div class="sidebar-content">
      <div id="treeContainer">{TREE_HTML}</div>
    </div>
  </div>
  <div class="right-panel">
    <div class="screenshot-panel">
      <h3>Screenshot</h3>
      <div class="screenshot-container" id="screenshotContainer">
        {SCREENSHOT_IMG}
      </div>
      <p><small>{SCREENSHOT_NAME}</small></p>
    </div>
    <div class="properties-panel">
      <div class="properties-header">
        <h3 style="margin:0;">Selected Node Properties</h3>
      </div>
      <div class="properties-content">
        <div id="props">Click a node in the tree to see its properties here.</div>
      </div>
    </div>
  </div>
</div>

<!-- Context Menus -->
<div id="treeContextMenu" class="context-menu">
  <div class="context-menu-item" onclick="copyToClipboard('realname')">Copy realname</div>
  <div class="context-menu-item" onclick="copyToClipboard('class')">Copy class</div>
  <div class="context-menu-item" onclick="copyToClipboard('objectName')">Copy objectName</div>
</div>

<div id="propsContextMenu" class="context-menu">
  <div class="context-menu-item" onclick="copyToClipboard('propName')">Copy property name</div>
  <div class="context-menu-item" onclick="copyToClipboard('propValue')">Copy property value</div>
</div>

<script>
function formatPropertiesAsTable(propsStr, searchTerm) {
    try {
        // Decode HTML entities first
        var textarea = document.createElement('textarea');
        textarea.innerHTML = propsStr;
        var decodedStr = textarea.value;
        
        var props = eval("(" + decodedStr + ")");
        if (typeof props !== 'object' || props === null) {
            return "<p>No properties available</p>";
        }
        
        searchTerm = searchTerm || "";
        
        // Group properties hierarchically
        var groups = {};
        var standalone = {};
        
        for (var key in props) {
            if (props.hasOwnProperty(key)) {
                var parts = key.split('_');
                if (parts.length > 1) {
                    var groupName = parts[0];
                    var propName = parts.slice(1).join('_');
                    if (!groups[groupName]) groups[groupName] = {};
                    groups[groupName][propName] = props[key];
                } else if (key === 'superclasses') {
                    // Split superclasses into individual items
                    if (!groups['superclasses']) groups['superclasses'] = {};
                    var classes = props[key].split(' > ');
                    for (var i = 0; i < classes.length; i++) {
                        groups['superclasses']['level_' + i] = classes[i];
                    }
                } else {
                    standalone[key] = props[key];
                }
            }
        }
        
        // Get sort order from dropdown (default: descending)
        var sortOrder = document.getElementById('sortOrder') ? document.getElementById('sortOrder').value : 'desc';
        
        // Sort function
        function sortKeys(obj) {
            var keys = Object.keys(obj);
            if (sortOrder === 'asc') {
                keys.sort();
            } else if (sortOrder === 'desc') {
                keys.sort().reverse();
            }
            // 'none' = no sorting, keep original order
            return keys;
        }
        
        var table = "<table class='props-table'>";
        table += "<thead><tr><th>Property</th><th>Value</th></tr></thead><tbody>";
        
        // Filter and add standalone properties first (sorted)
        var standaloneKeys = sortKeys(standalone);
        for (var i = 0; i < standaloneKeys.length; i++) {
            var key = standaloneKeys[i];
            var value = standalone[key];
            if (value === null || value === undefined) value = "";
            
            // Apply search filter
            if (searchTerm === "" || 
                key.toLowerCase().includes(searchTerm) || 
                value.toString().toLowerCase().includes(searchTerm)) {
                table += "<tr><td>" + key + "</td><td>" + value + "</td></tr>";
            }
        }
        
        // Filter and add grouped properties with hierarchy (sorted groups)
        var groupKeys = sortKeys(groups);
        for (var i = 0; i < groupKeys.length; i++) {
            var groupName = groupKeys[i];
            var groupHasMatches = false;
            var groupContent = "";
            
            // Sort properties within each group and check for matches
            var groupPropKeys = sortKeys(groups[groupName]);
            for (var j = 0; j < groupPropKeys.length; j++) {
                var propName = groupPropKeys[j];
                var value = groups[groupName][propName];
                if (value === null || value === undefined) value = "";
                var displayName = propName.replace('level_', 'inheritance_');
                
                // Apply search filter
                if (searchTerm === "" || 
                    groupName.toLowerCase().includes(searchTerm) ||
                    displayName.toLowerCase().includes(searchTerm) || 
                    value.toString().toLowerCase().includes(searchTerm)) {
                    groupContent += "<tr class='group-item'><td>&nbsp;&nbsp;&nbsp;&nbsp;" + displayName + "</td><td>" + value + "</td></tr>";
                    groupHasMatches = true;
                }
            }
            
            // Only add group if it has matches
            if (groupHasMatches) {
                table += "<tr class='group-header'><td colspan='2'><strong>" + groupName + "</strong></td></tr>";
                table += groupContent;
            }
        }
        
        table += "</tbody></table>";
        
        // Add click handlers to table rows after table is created
        setTimeout(function() {
            var tableRows = document.querySelectorAll('.props-table tr:not(.group-header)');
            tableRows.forEach(function(row) {
                row.addEventListener('click', function() {
                    // Remove selection from all rows
                    document.querySelectorAll('.props-table tr').forEach(function(r) {
                        r.classList.remove('selected');
                    });
                    // Add selection to clicked row
                    this.classList.add('selected');
                });
            });
        }, 10);
        
        return table;
    } catch(e) {
        return "<p class='props'>" + propsStr + "</p>";
    }
}

var currentSelectedNode = null;

var originalTreeHTML = "";
var currentPropsData = null;
var currentContextNode = null;
var currentContextPropName = null;
var currentContextPropValue = null;
var screenshotGeometry = null;

function refreshProperties() {
    if (currentSelectedNode) {
        var props = currentSelectedNode.getAttribute("data-props") || "{{}}";
        currentPropsData = props;
        filterAndDisplayProperties();
        updateElementOverlay();
    }
}

function updateElementOverlay() {
    // Remove existing overlay
    var existingOverlay = document.getElementById('elementOverlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }
    
    if (!currentSelectedNode) return; 
    
    var props = currentSelectedNode.getAttribute("data-props") || "{{}}";
    try {
        var textarea = document.createElement('textarea');
        textarea.innerHTML = props;
        var decodedStr = textarea.value;
        var propsObj = eval("(" + decodedStr + ")");
        
        // Check if element has geometry properties
        var elemX = propsObj['geometry_x'];
        var elemY = propsObj['geometry_y'];
        var elemWidth = propsObj['geometry_width'];
        var elemHeight = propsObj['geometry_height'];
        
        if (elemX !== undefined && elemY !== undefined && elemWidth !== undefined && elemHeight !== undefined) {
            // Get screenshot geometry (assume first element or root has the screenshot dimensions)
            if (!screenshotGeometry) {
                // Try to find screenshot geometry from the first element with geometry
                var allNodes = document.querySelectorAll('.node');
                for (var i = 0; i < allNodes.length; i++) {
                    var nodeProps = allNodes[i].getAttribute("data-props") || "{{}}";
                    try {
                        var nodeTextarea = document.createElement('textarea');
                        nodeTextarea.innerHTML = nodeProps;
                        var nodeDecoded = nodeTextarea.value;
                        var nodePropsObj = eval("(" + nodeDecoded + ")");
                        if (nodePropsObj['geometry_x'] !== undefined) {
                            screenshotGeometry = {
                                x: parseInt(nodePropsObj['geometry_x']) || 0,
                                y: parseInt(nodePropsObj['geometry_y']) || 0
                            };
                            break;
                        }
                    } catch(e) {}
                }
                if (!screenshotGeometry) {
                    screenshotGeometry = {x: 0, y: 0}; // Default fallback
                }
            }
            
            drawElementOverlay(
                parseInt(elemX) - screenshotGeometry.x,
                parseInt(elemY) - screenshotGeometry.y,
                parseInt(elemWidth),
                parseInt(elemHeight)
            );
        }
    } catch(e) {
        console.log('Error parsing properties for overlay:', e);
    }
}

function drawElementOverlay(x, y, width, height) {
    var screenshotImg = document.querySelector('.screenshot');
    var container = document.getElementById('screenshotContainer');
    
    if (!screenshotImg || !container) return;
    
    // Screenshot is always visible now
    
    // Get actual displayed image dimensions
    var imgRect = screenshotImg.getBoundingClientRect();
    var containerRect = container.getBoundingClientRect();
    
    // Calculate scale factor between actual image and displayed image
    var scaleX = imgRect.width / screenshotImg.naturalWidth;
    var scaleY = imgRect.height / screenshotImg.naturalHeight;
    
    // Calculate overlay position and size
    var overlayX = x * scaleX;
    var overlayY = y * scaleY;
    var overlayWidth = width * scaleX;
    var overlayHeight = height * scaleY;
    
    // Create overlay element
    var overlay = document.createElement('div');
    overlay.id = 'elementOverlay';
    overlay.className = 'element-overlay';
    overlay.style.left = overlayX + 'px';
    overlay.style.top = overlayY + 'px';
    overlay.style.width = overlayWidth + 'px';
    overlay.style.height = overlayHeight + 'px';
    
    container.appendChild(overlay);
}

function filterAndDisplayProperties() {
    if (!currentPropsData) return;
    
    var searchTerm = document.getElementById('propsSearch').value.toLowerCase();
    var html = formatPropertiesAsTable(currentPropsData, searchTerm);
    document.getElementById("props").innerHTML = html;
}

function filterTree() {
    var searchTerm = document.getElementById('treeSearch').value.toLowerCase();
    var treeContainer = document.getElementById('treeContainer');
    
    if (searchTerm === '') {
        // Show all nodes
        var allNodes = treeContainer.querySelectorAll('li');
        allNodes.forEach(function(node) {
            node.style.display = '';
        });
        var allUls = treeContainer.querySelectorAll('ul');
        allUls.forEach(function(ul) {
            ul.style.display = '';
        });
    } else {
        // Hide all nodes first
        var allNodes = treeContainer.querySelectorAll('li');
        allNodes.forEach(function(node) {
            node.style.display = 'none';
        });
        
        // Show matching nodes and their parents
        var nodeSpans = treeContainer.querySelectorAll('.node');
        nodeSpans.forEach(function(span) {
            if (span.textContent.toLowerCase().includes(searchTerm)) {
                // Show this node and all its parents
                var current = span.closest('li');
                while (current) {
                    current.style.display = '';
                    // Show parent ul and li
                    var parentUl = current.parentElement;
                    if (parentUl && parentUl.tagName === 'UL') {
                        parentUl.style.display = '';
                        var parentLi = parentUl.parentElement;
                        if (parentLi && parentLi.tagName === 'LI') {
                            parentLi.style.display = '';
                            current = parentLi;
                        } else {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
        });
    }
}

document.addEventListener("click", function(e){
    if(e.target.classList.contains("node")){
        document.querySelectorAll(".node").forEach(n=>n.classList.remove("selected"));
        e.target.classList.add("selected");
        currentSelectedNode = e.target;
        var props = e.target.getAttribute("data-props") || "{{}}";
        currentPropsData = props;
        filterAndDisplayProperties();
        updateElementOverlay();
    }

});

// Add context menu event listeners after DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
    // Tree context menu
    document.addEventListener('contextmenu', function(e) {
        if (e.target.classList.contains('node')) {
            showTreeContextMenu(e, e.target);
        }
    });
    
    // Properties table context menu  
    document.addEventListener('contextmenu', function(e) {
        var targetCell = e.target.closest('.props-table td');
        if (targetCell) {
            var row = targetCell.parentElement;
            // Ensure it's a property row, not a group header
            if (row.cells.length === 2) {
                var propName = row.cells[0].textContent.trim();
                var propValue = row.cells[1].textContent.trim();
                showPropsContextMenu(e, propName, propValue);
            }
        }
    });
});

// Add search functionality
document.getElementById("treeSearch").addEventListener("input", function() {
    filterTree();
    toggleClearButton('treeSearch', 'clearTreeSearch');
});
document.getElementById("propsSearch").addEventListener("input", function() {
    filterAndDisplayProperties();
    toggleClearButton('propsSearch', 'clearPropsSearch');
});

function toggleClearButton(inputId, buttonId) {
    var input = document.getElementById(inputId);
    var button = document.getElementById(buttonId);
    if (input.value.length > 0) {
        button.style.display = 'block';
    } else {
        button.style.display = 'none';
    }
}

function clearTreeSearch() {
    var input = document.getElementById('treeSearch');
    input.value = '';
    input.focus();
    filterTree();
    toggleClearButton('treeSearch', 'clearTreeSearch');
}

function clearPropsSearch() {
    var input = document.getElementById('propsSearch');
    input.value = '';
    input.focus();
    filterAndDisplayProperties();
    toggleClearButton('propsSearch', 'clearPropsSearch');
}

// Initialize original tree HTML and context menus
document.addEventListener("DOMContentLoaded", function() {
    originalTreeHTML = document.getElementById('treeContainer').innerHTML;
});

// Update overlay when window is resized
window.addEventListener('resize', function() {
    setTimeout(updateElementOverlay, 100);
});

// Context menu functions
function copyToClipboard(type) {
    var textToCopy = "";
    var what = "";

    if (type === 'realname' || type === 'class' || type === 'objectName') {
        what = type;
        if (currentContextNode) {
            var props = currentContextNode.getAttribute("data-props") || "{{}}";
            try {
                var textarea = document.createElement('textarea');
                textarea.innerHTML = props;
                var decodedStr = textarea.value;
                var propsObj = eval("(" + decodedStr + ")");
                textToCopy = propsObj[type] || "";
            } catch(e) {
                textToCopy = "Property not found";
            }
        }
    } else if (type === 'propName') {
        what = "Property name";
        textToCopy = currentContextPropName || "";
    } else if (type === 'propValue') {
        what = "Property value";
        textToCopy = currentContextPropValue || "";
    }

    function showToast(message) {
        var feedback = document.createElement('div');
        feedback.textContent = message;
        feedback.style.cssText = 'position:fixed;top:20px;right:20px;background:#2c3e50;color:white;padding:10px 20px;border-radius:4px;z-index:10000;font-family:Arial,sans-serif;font-size:14px;';
        document.body.appendChild(feedback);
        setTimeout(function() { document.body.removeChild(feedback); }, 2500);
    }

    if (textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(function() {
            var shortText = textToCopy.length > 50 ? textToCopy.substring(0, 47) + '...' : textToCopy;
            showToast('Copied "' + shortText + '" to clipboard.');
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            // Fallback for older browsers
            var textArea = document.createElement('textarea');
            textArea.value = textToCopy;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                var shortText = textToCopy.length > 50 ? textToCopy.substring(0, 47) + '...' : textToCopy;
                showToast('Copied "' + shortText + '" to clipboard.');
            } catch (copyErr) {
                showToast('Failed to copy.');
            }
            document.body.removeChild(textArea);
        });
    }
    
    hideContextMenus();
}

function hideContextMenus() {
    document.getElementById('treeContextMenu').style.display = 'none';
    document.getElementById('propsContextMenu').style.display = 'none';
}

function showTreeContextMenu(e, node) {
    e.preventDefault();
    currentContextNode = node;
    var menu = document.getElementById('treeContextMenu');
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
}

function showPropsContextMenu(e, propName, propValue) {
    e.preventDefault();
    currentContextPropName = propName;
    currentContextPropValue = propValue;
    var menu = document.getElementById('propsContextMenu');
    menu.style.display = 'block';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
}

function getSelectedNodeXml() {
    if (currentSelectedNode) {
        var xml_string = currentSelectedNode.getAttribute("data-xml");
        if (xml_string) {
            // Decode HTML entities
            var textarea = document.createElement('textarea');
            textarea.innerHTML = xml_string;
            return textarea.value;
        }
    }
    return null;
}



function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}



// Hide context menus when clicking elsewhere
document.addEventListener('click', hideContextMenus);
document.addEventListener('contextmenu', function(e) {
    if (!e.target.closest('.context-menu')) {
        hideContextMenus();
    }
});


</script>

<!-- Hidden XML data for copying -->
<div id="rawXmlData" style="display:none;">{RAW_XML}</div>



</body>
</html>
'''
    
    # First, fix CSS double curly braces to single curly braces
    html = html_template.replace('{{', '{').replace('}}', '}')
    
    # Replace placeholders with actual values using simple string replacement
    html = html.replace('{TITLE}', title)
    html = html.replace('{TREE_HTML}', tree_html)
    html = html.replace('{SCREENSHOT_IMG}', screenshot_img)
    html = html.replace('{SCREENSHOT_NAME}', escape(screenshot_name))
    html = html.replace('{RAW_XML}', escape(raw_xml))
    
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("Wrote HTML viewer to:", html_path)

class SquishXMLViewerDesktop:
    def __init__(self):
        self.current_xml_path = None
        self.html_content = None
        self.window = None
    
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
            print("File dialog not available.")
    
    def load_xml_file(self, xml_path):
        """Load XML file and display in desktop window"""
        try:
            self.current_xml_path = xml_path
            
            # Generate HTML content using the existing generate_html_content function
            title, tree_html, screenshot_img, screenshot_name, raw_xml = generate_html_content(xml_path)
            
            # Use the same HTML template but modify for desktop
            self.html_content = generate_desktop_html(title, tree_html, screenshot_img, screenshot_name, raw_xml)
            
            if WEBVIEW_AVAILABLE and self.window:
                self.window.load_html(self.html_content)
            else:
                # Fallback: write to file and open in browser
                import tempfile
                import webbrowser
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
    
    def show_about(self):
        """Show about dialog"""
        if WEBVIEW_AVAILABLE and self.window:
            self.window.evaluate_js('''
                alert("Squish XML Viewer Desktop\\n\\nA desktop application for viewing Squish XML snapshot files.\\n\\nFeatures:\\n- Interactive object tree navigation\\n- Property inspection\\n- Screenshot visualization with element overlay\\n- Click-to-highlight functionality\\n\\nBuilt with Python and pywebview.");
            ''')
        else:
            print("About: Squish XML Viewer Desktop")
    
    def exit_app(self):
        """Exit application"""
        if WEBVIEW_AVAILABLE and self.window:
            self.window.destroy()
        else:
            import sys
            sys.exit(0)
    
    def run(self, xml_path=None):
        """Run the desktop application"""
        if WEBVIEW_AVAILABLE:
            # Generate initial HTML
            if xml_path and os.path.isfile(xml_path):
                title, tree_html, screenshot_img, screenshot_name, raw_xml = generate_html_content(xml_path)
                initial_html = generate_desktop_html(title, tree_html, screenshot_img, screenshot_name, raw_xml)
            else:
                initial_html = get_welcome_html()
            
            # Create webview window
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
            # Fallback to original browser mode
            if xml_path and os.path.isfile(xml_path):
                out_html = os.path.splitext(xml_path)[0] + "_viewer.html"
                generate_html(xml_path, out_html)
            else:
                print("Please provide an XML file path as argument")
                print("Usage: python3 squish_xml_viewer_desktop.py path/to/file.xml")

def generate_html_content(xml_path):
    """Extract the content generation logic for reuse"""
    obj_root = parse_object_xml(xml_path)
    if obj_root is None:
        raise Exception("Failed to parse XML file")
    
    image_base64 = extract_image_from_element(obj_root)
    title = f"Squish XML Viewer - {os.path.basename(xml_path)}"
    tree_html = build_tree_html(obj_root)[0] if obj_root is not None else "<p>No tree structure found.</p>"
    tree_html = "<ul class='tree'>\n" + tree_html + "\n</ul>"
    
    if image_base64:
        screenshot_img = f'<img id="screenshot" src="data:image/png;base64,{image_base64}" style="max-width: 100%; cursor: crosshair;" />'
        screenshot_name = os.path.basename(xml_path)
    else:
        screenshot_img = '<p style="color: #999; text-align: center; padding: 50px;">No screenshot available in this XML file.</p>'
        screenshot_name = "No screenshot"
    
    # Read raw XML for display
    with open(xml_path, 'r', encoding='utf-8') as f:
        raw_xml = f.read()
    
    return title, tree_html, screenshot_img, screenshot_name, raw_xml

def generate_desktop_html(title, tree_html, screenshot_img, screenshot_name, raw_xml):
    """Generate HTML specifically for desktop window (same as original)"""
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>{TITLE}</title>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #f5f5f5;
        }}
        .container {{
            display: flex;
            height: 100vh;
        }}
        .left-panel {{
            width: 350px;
            background: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
            padding: 15px;
        }}
        .right-panel {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .screenshot-container {{
            flex: 1;
            background: white;
            margin: 10px;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: auto;
            position: relative;
        }}
        .properties-panel {{
            height: 200px;
            background: white;
            margin: 0 10px 10px 10px;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow-y: auto;
        }}
        .tree-item {{
            margin-left: 20px;
        }}
        .tree-node {{
            cursor: pointer;
            padding: 4px 8px;
            margin: 2px 0;
            border-radius: 4px;
            display: inline-block;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 13px;
        }}
        .tree-node:hover {{
            background: #e3f2fd;
        }}
        .tree-node.selected {{
            background: #2196f3;
            color: white;
        }}
        .tree-children {{
            margin-left: 15px;
        }}
        h2 {{
            margin-top: 0;
            color: #333;
            font-size: 18px;
        }}
        .properties-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        .properties-table th, .properties-table td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .properties-table th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        .element-overlay {{
            position: absolute;
            border: 2px solid red;
            background: rgba(255, 0, 0, 0.1);
            pointer-events: none;
            z-index: 1000;
        }}
        .search-box {{
            width: 100%;
            padding: 8px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="left-panel">
            <input type="text" id="searchBox" class="search-box" placeholder="Search elements..." onkeyup="searchTree()">
            <h2>Object Tree</h2>
            <div id="tree">
                {TREE_HTML}
            </div>
        </div>
        <div class="right-panel">
            <div class="screenshot-container" id="screenshotContainer">
                <h2>{SCREENSHOT_NAME}</h2>
                {SCREENSHOT_IMG}
            </div>
            <div class="properties-panel">
                <h2>Properties</h2>
                <table class="properties-table" id="propertiesTable">
                    <thead>
                        <tr>
                            <th>Property</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td colspan="2">Select an element in the tree to view its properties</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let selectedElement = null;
        let allElements = [];
        
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
        
        function selectElement(path, x, y, width, height) {{
            if (selectedElement) {{
                selectedElement.classList.remove('selected');
            }}
            
            selectedElement = document.querySelector(`[data-path="${{path}}"]`).querySelector('.tree-node');
            selectedElement.classList.add('selected');
            
            updateElementOverlay(parseInt(x), parseInt(y), parseInt(width), parseInt(height));
            updateElementProperties(path, x, y, width, height);
        }}
        
        function updateElementOverlay(x, y, width, height) {{
            const existingOverlay = document.querySelector('.element-overlay');
            if (existingOverlay) {{
                existingOverlay.remove();
            }}
            
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
        
        function updateElementProperties(path, x, y, width, height) {{
            const table = document.getElementById('propertiesTable').querySelector('tbody');
            table.innerHTML = '';
            
            const properties = {{
                'Path': path,
                'X': x,
                'Y': y,
                'Width': width,
                'Height': height
            }};
            
            for (const [key, value] of Object.entries(properties)) {{
                const row = table.insertRow();
                row.innerHTML = `<td><strong>${{key}}</strong></td><td>${{value}}</td>`;
            }}
        }}
        
        document.addEventListener('DOMContentLoaded', function() {{
            allElements = [];
            document.querySelectorAll('[data-path]').forEach(elem => {{
                allElements.push({{
                    element: elem,
                    text: elem.textContent.toLowerCase(),
                    path: elem.getAttribute('data-path')
                }});
            }});
        }});
    </script>
</body>
</html>"""
    
    # Replace placeholders
    html = html_template.replace('{TITLE}', title)
    html = html.replace('{TREE_HTML}', tree_html)
    html = html.replace('{SCREENSHOT_IMG}', screenshot_img)
    html = html.replace('{SCREENSHOT_NAME}', escape(screenshot_name))
    
    return html

def get_welcome_html():
    """Generate welcome screen for desktop app"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Squish XML Viewer Desktop</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f5f5f5; }
            .welcome { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }
            .logo { font-size: 48px; margin-bottom: 20px; }
            h1 { color: #2c3e50; margin-bottom: 10px; }
            p { color: #7f8c8d; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="welcome">
            <div class="logo">📁</div>
            <h1>Squish XML Viewer Desktop</h1>
            <p>Please provide an XML file as command line argument to start viewing.</p>
            <p><code>python squish_xml_viewer_desktop.py path/to/file.xml</code></p>
        </div>
    </body>
    </html>
    '''

def main():
    if WEBVIEW_AVAILABLE:
        # Desktop mode
        app = SquishXMLViewerDesktop()
        xml_path = None
        if len(sys.argv) > 1:
            xml_path = sys.argv[1]
            if not os.path.isfile(xml_path):
                print("XML file not found:", xml_path)
                sys.exit(2)
        app.run(xml_path)
    else:
        # Original browser mode fallback
        if len(sys.argv) < 2:
            print("Usage: python3 squish_xml_viewer_desktop.py path/to/file.xml")
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
