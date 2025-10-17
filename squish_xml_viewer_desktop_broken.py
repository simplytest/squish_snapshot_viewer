#!/usr/bin/env python3
"""
squish_xml_viewer_desktop.py

Desktop version of the Squish XML Viewer using pywebview.
Creates a native desktop application with file menu for opening XML snapshots.

Requirements:
    pip install pywebview

Usage:
    python3 squish_xml_viewer_desktop.py [path/to/snapshot.xml]

Features:
    - Native desktop window (no browser UI)
    - File menu with "Open XML Snapshot" option
    - Same UI and functionality as web version
    - Drag & drop support for XML files
"""

import sys
import os
import base64
import xml.etree.ElementTree as ET
from html import escape
import tempfile
import threading
import webbrowser
import json
from urllib.parse import quote

# Try to import webview, fall back to browser if not available
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("Warning: pywebview not installed. Falling back to browser mode.")
    print("Install with: pip install pywebview")

# Import the core functions from the original script
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

def generate_html_content(xml_path):
    """Generate HTML content for the viewer"""
    xml_root = parse_object_xml(xml_path)
    if xml_root is None:
        return None

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
  <h1>Squish XML Viewer</h1>
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
        var props = currentSelectedNode.getAttribute("data-props") || "{}";
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
    
    var props = currentSelectedNode.getAttribute("data-props") || "{}";
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
                    var nodeProps = allNodes[i].getAttribute("data-props") || "{}";
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
        var props = e.target.getAttribute("data-props") || "{}";
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
            var props = currentContextNode.getAttribute("data-props") || "{}";
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
    
    return html

class SquishXMLViewerDesktop:
    """Desktop application for viewing Squish XML snapshots"""
    
    def __init__(self):
        self.current_xml_path = None
        self.html_content = None
        self.current_folder = None
        self.xml_files_in_folder = []
        
        
    def get_welcome_html(self):
        """Get the welcome screen HTML with full menu"""
        return '''
        <html>
        <head>
            <style>
                body { font-family: Arial; margin: 0; padding: 0; background: #f8f9fa; }
                .menu-bar {
                    background: #2c3e50;
                    color: white;
                    padding: 8px 0;
                    border-bottom: 1px solid #34495e;
                }
                .menu-item {
                    display: inline-block;
                    position: relative;
                    padding: 8px 16px;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                .menu-item:hover {
                    background: #34495e;
                }
                .dropdown {
                    display: none;
                    position: absolute;
                    top: 100%;
                    left: 0;
                    background: white;
                    color: black;
                    min-width: 200px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    z-index: 1000;
                    border: 1px solid #bdc3c7;
                }
                .dropdown-item {
                    padding: 8px 16px;
                    cursor: pointer;
                    border-bottom: 1px solid #ecf0f1;
                }
                .dropdown-item:hover {
                    background: #ecf0f1;
                }
                .dropdown-item.disabled {
                    color: #95a5a6;
                    cursor: not-allowed;
                }
                .dropdown-item.disabled:hover {
                    background: transparent;
                }
                .separator {
                    height: 1px;
                    background: #bdc3c7;
                    margin: 4px 0;
                }
                .content {
                    padding: 40px;
                    text-align: center;
                }
                .open-button {
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin: 10px;
                }
                .open-button:hover {
                    background: #2980b9;
                }
            </style>
        </head>
        <body>
            <div class="menu-bar">
                <div class="menu-item" onmouseenter="showDropdown('file-menu')" onmouseleave="scheduleHideDropdown('file-menu')">
                    File
                    <div id="file-menu" class="dropdown" onmouseenter="cancelHideDropdown()" onmouseleave="scheduleHideDropdown('file-menu')">
                        <div class="dropdown-item" onclick="openFile()">Open XML Snapshot...</div>
                        <div class="dropdown-item" onclick="openFolder()">Open Folder...</div>
                        <div class="dropdown-item disabled">Close</div>
                        <div class="separator"></div>
                        <div class="dropdown-item" onclick="exitApp()">Exit</div>
                    </div>
                </div>
                <div class="menu-item" onmouseenter="showDropdown('help-menu')" onmouseleave="scheduleHideDropdown('help-menu')">
                    Help
                    <div id="help-menu" class="dropdown" onmouseenter="cancelHideDropdown()" onmouseleave="scheduleHideDropdown('help-menu')">
                        <div class="dropdown-item" onclick="showAbout()">About</div>
                    </div>
                </div>
            </div>
            
            <div class="content">
                <h1 style="color: #2c3e50;">Squish XML Viewer</h1>
                <p style="font-size: 18px; color: #7f8c8d; margin: 20px 0;">
                    Desktop application for viewing Squish XML snapshots
                </p>
                
                <!-- Drop Zone -->
                <div id="drop-zone" style="
                    border: 3px dashed #bdc3c7;
                    border-radius: 10px;
                    padding: 40px;
                    margin: 20px auto;
                    max-width: 500px;
                    text-align: center;
                    background: #ecf0f1;
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onclick="openFile()">
                    <div style="font-size: 48px; color: #95a5a6; margin-bottom: 15px;">📁</div>
                    <h3 style="color: #2c3e50; margin: 10px 0;">Drop XML file here</h3>
                    <p style="color: #7f8c8d; margin: 5px 0;">or click to browse</p>
                    <p style="color: #95a5a6; font-size: 14px;">Supports .xml files</p>
                </div>
                
                <div style="margin: 40px 0;">
                    <button class="open-button" onclick="openFile()">
                        Open XML Snapshot...
                    </button>
                </div>
                <p style="color: #95a5a6; font-size: 14px;">
                    Use the File menu or drag & drop an XML file to get started
                </p>
            </div>
            
            <script>
                let currentDropdown = null;
                let hideTimeout = null;
                
                function showDropdown(id) {
                    if (hideTimeout) {
                        clearTimeout(hideTimeout);
                        hideTimeout = null;
                    }
                    hideAllDropdowns();
                    document.getElementById(id).style.display = 'block';
                    currentDropdown = id;
                }
                
                function scheduleHideDropdown(id) {
                    hideTimeout = setTimeout(() => {
                        if (currentDropdown === id) {
                            document.getElementById(id).style.display = 'none';
                            currentDropdown = null;
                        }
                    }, 300);
                }
                
                function cancelHideDropdown() {
                    if (hideTimeout) {
                        clearTimeout(hideTimeout);
                        hideTimeout = null;
                    }
                }
                
                function hideAllDropdowns() {
                    const dropdowns = document.querySelectorAll('.dropdown');
                    dropdowns.forEach(dropdown => dropdown.style.display = 'none');
                    currentDropdown = null;
                }
                
                function openFile() {
                    hideAllDropdowns();
                    if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
                    if (window.pywebview && window.pywebview.api) { 
                        window.pywebview.api.open_file_dialog();
                    }
                }
                
                function openFolder() {
                    hideAllDropdowns();
                    if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
                    if (window.pywebview && window.pywebview.api) { 
                        window.pywebview.api.open_folder_dialog();
                    }
                }
                
                function showAbout() {
                    hideAllDropdowns();
                    if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
                    if (window.pywebview && window.pywebview.api) { 
                        window.pywebview.api.show_about();
                    }
                }
                
                function exitApp() {
                    hideAllDropdowns();
                    if (hideTimeout) { clearTimeout(hideTimeout); hideTimeout = null; }
                    if (window.pywebview && window.pywebview.api) { 
                        window.pywebview.api.exit_app();
                    }
                }
                
                document.addEventListener('click', hideAllDropdowns);
                
                
                // Drag and Drop functionality
                document.addEventListener('DOMContentLoaded', function() {
                    const body = document.body;
                    const dropZone = document.getElementById('drop-zone');
                    
                    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                        body.addEventListener(eventName, e => { e.preventDefault(); e.stopPropagation(); }, false);
                    });
                    
                    ['dragenter', 'dragover'].forEach(eventName => {
                        body.addEventListener(eventName, () => {
                            if (dropZone) {
                                dropZone.style.borderColor = '#3498db';
                                dropZone.style.backgroundColor = '#e3f2fd';
                                dropZone.style.transform = 'scale(1.02)';
                            }
                        }, false);
                    });
                    
                    ['dragleave', 'drop'].forEach(eventName => {
                        body.addEventListener(eventName, () => {
                            if (dropZone) {
                                dropZone.style.borderColor = '#bdc3c7';
                                dropZone.style.backgroundColor = '#ecf0f1';
                                dropZone.style.transform = 'scale(1)';
                            }
                        }, false);
                    });
                    
                    body.addEventListener('drop', (e) => {
                        const files = e.dataTransfer.files;
                        if (files.length > 0) {
                            const file = files[0];
                            if (file.name.toLowerCase().endsWith('.xml')) {
                                if (dropZone) {
                                    dropZone.innerHTML = '<div style="font-size: 48px; color: #3498db;">⏳</div><h3>Loading...</h3><p>Please use File → Open to select this file</p>';
                                }
                                setTimeout(() => openFile(), 1000);
                            } else {
                                alert('Please drop an XML file (.xml extension required).');
                            }
                        }
                    }, false);
                });
            </script>
        </body>
        </html>
        '''
        
    def open_file_dialog(self):
        """Open file dialog to select XML file"""
        if WEBVIEW_AVAILABLE:
            try:
                # Use the new pywebview 6.0+ API directly
                result = webview.windows[0].create_file_dialog(
                    webview.FileDialog.OPEN,
                    allow_multiple=False,
                    file_types=('XML Files (*.xml)', 'All files (*.*)')
                )
                if result and len(result) > 0:
                    xml_path = result[0]
                    self.load_xml_file(xml_path)
            except Exception as e:
                print(f"File dialog error: {e}")
                # Fallback: show instruction message
                if WEBVIEW_AVAILABLE:
                    webview.windows[0].evaluate_js('''
                        alert("File dialog not available. Please drag & drop an XML file instead.");
                    ''')
        else:
            print("File dialog not available in browser mode. Please provide XML file as command line argument.")
            print("Usage: python3 squish_xml_viewer_desktop.py path/to/file.xml")
    
    def close_file(self):
        """Close current file"""
        self.current_xml_path = None
        self.html_content = None
        if WEBVIEW_AVAILABLE:
            # Load the welcome screen with menu (same as startup)
            initial_html = self.get_welcome_html()
            webview.windows[0].load_html(initial_html)
        else:
            print("File closed.")
    
    def exit_app(self):
        """Exit application"""
        if WEBVIEW_AVAILABLE:
            webview.windows[0].destroy()
        else:
            sys.exit(0)
    
    def add_menu_to_html(self, html_content):
        """Add simple menu bar to existing HTML content"""
        menu_bar = '''
        <div style="background: #2c3e50; color: white; padding: 8px 16px; border-bottom: 1px solid #34495e; font-family: -apple-system, BlinkMacSystemFont, sans-serif;">
            <span style="font-weight: 600;">📁 Squish XML Viewer</span>
            <span style="margin-left: 20px; font-size: 14px; color: #bdc3c7;">
                Right-click for context menu | Click elements in Object Tree to highlight on screenshot
            </span>
        </div>
        '''
        
        # Insert menu right after <body> tag
        if '<body' in html_content:
            body_start = html_content.find('>', html_content.find('<body')) + 1
            html_content = html_content[:body_start] + menu_bar + html_content[body_start:]
        
        return html_content
                     onmouseenter="cancelHideDropdown()" onmouseleave="scheduleHideDropdown('file-menu')">
                    <div class="dropdown-item" style="padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #ecf0f1;" onclick="openFile()">Open XML Snapshot...</div>
                    <div class="dropdown-item" style="padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #ecf0f1;" onclick="openFolder()">Open Folder...</div>
                    <div class="dropdown-item" style="padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #ecf0f1;" onclick="closeFile()">Close</div>
                    <div class="separator" style="height: 1px; background: #bdc3c7; margin: 4px 0;"></div>
                    <div class="dropdown-item" style="padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #ecf0f1;" onclick="exitApp()">Exit</div>
                </div>
            </div>
            <div class="menu-item" style="display: inline-block; position: relative; padding: 8px 16px; cursor: pointer;" 
                 onmouseenter="showDropdown('help-menu')" onmouseleave="scheduleHideDropdown('help-menu')">
                Help
                <div id="help-menu" class="dropdown" style="display: none; position: absolute; top: 100%; left: 0; background: white; color: black; min-width: 200px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); z-index: 1000; border: 1px solid #bdc3c7;"
                     onmouseenter="cancelHideDropdown()" onmouseleave="scheduleHideDropdown('help-menu')">
                    <div class="dropdown-item" style="padding: 8px 16px; cursor: pointer; border-bottom: 1px solid #ecf0f1;" onclick="showAbout()">About</div>
                </div>
            </div>
        </div>
        '''
        
        menu_script = '''
        <script>
            let currentDropdown = null;
            let hideTimeout = null;
            
            function showDropdown(id) {
                // Cancel any pending hide
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                
                hideAllDropdowns();
                document.getElementById(id).style.display = 'block';
                currentDropdown = id;
            }
            
            function scheduleHideDropdown(id) {
                // Delay hiding to allow mouse to move into dropdown
                hideTimeout = setTimeout(() => {
                    if (currentDropdown === id) {
                        document.getElementById(id).style.display = 'none';
                        currentDropdown = null;
                    }
                }, 300); // 300ms delay
            }
            
            function cancelHideDropdown() {
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
            }
            
            function hideDropdown(id) {
                document.getElementById(id).style.display = 'none';
                currentDropdown = null;
            }
            
            function hideAllDropdowns() {
                const dropdowns = document.querySelectorAll('.dropdown');
                dropdowns.forEach(dropdown => dropdown.style.display = 'none');
                currentDropdown = null;
            }
            
            function openFile() {
                hideAllDropdowns();
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.open_file_dialog();
                }
            }
            
            function openFolder() {
                hideAllDropdowns();
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.open_folder_dialog();
                }
            }
            
            function closeFile() {
                hideAllDropdowns();
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.close_file();
                }
            }
            
            function showAbout() {
                hideAllDropdowns();
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.show_about();
                }
            }
            
            function exitApp() {
                hideAllDropdowns();
                if (hideTimeout) {
                    clearTimeout(hideTimeout);
                    hideTimeout = null;
                }
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.exit_app();
                }
            }
            
            // Hide dropdowns when clicking elsewhere
            document.addEventListener('click', hideAllDropdowns);
            
            // Menu hover effects
            document.querySelectorAll('.menu-item').forEach(item => {
                item.addEventListener('mouseenter', function() {
                    this.style.background = '#34495e';
                });
                item.addEventListener('mouseleave', function() {
                    this.style.background = 'transparent';
                });
            });
            
            document.querySelectorAll('.dropdown-item:not(.disabled)').forEach(item => {
                item.addEventListener('mouseenter', function() {
                    this.style.background = '#ecf0f1';
                });
                item.addEventListener('mouseleave', function() {
                    this.style.background = 'transparent';
                });
            });
            
            // Drag and Drop functionality
            document.addEventListener('DOMContentLoaded', function() {
                const body = document.body;
                
                // Prevent default drag behaviors
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    body.addEventListener(eventName, preventDefaults, false);
                    document.addEventListener(eventName, preventDefaults, false);
                });
                
                // Highlight drop area
                ['dragenter', 'dragover'].forEach(eventName => {
                    body.addEventListener(eventName, highlight, false);
                });
                
                ['dragleave', 'drop'].forEach(eventName => {
                    body.addEventListener(eventName, unhighlight, false);
                });
                
                // Handle dropped files
                body.addEventListener('drop', handleDrop, false);
                
                function preventDefaults(e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                
                function highlight(e) {
                    body.style.backgroundColor = '#e3f2fd';
                    body.style.border = '2px dashed #2196f3';
                }
                
                function unhighlight(e) {
                    body.style.backgroundColor = '';
                    body.style.border = '';
                }
                
                function handleDrop(e) {
                    const dt = e.dataTransfer;
                    const files = dt.files;
                    
                    if (files.length > 0) {
                        const file = files[0];
                        if (file.name.toLowerCase().endsWith('.xml')) {
                            // In webview, we need to handle file paths differently
                            if (window.pywebview) {
                                // For security reasons, we can't directly access file paths
                                // Instead, we'll show a message and ask user to use File menu
                                alert('Please use File → Open XML Snapshot... to open XML files.');
                            }
                        } else {
                            alert('Please drop an XML file (.xml extension required).');
                        }
                    }
                }
            });
        </script>
        '''
        
        # Insert menu after body tag
        if '<body' in html_content:
            body_start = html_content.find('<body')
            body_end = html_content.find('>', body_start) + 1
            html_content = html_content[:body_end] + menu_bar + html_content[body_end:]
        
        # Insert script before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', menu_script + '</body>')
        
        return html_content
    def load_xml_file(self, xml_path):
        """Load and display XML file"""
        try:
            self.current_xml_path = xml_path
            self.html_content = generate_html_content(xml_path)
            
            if self.html_content:
                # Add menu to HTML content
                self.html_content = self.add_menu_to_html(self.html_content)
                
                if WEBVIEW_AVAILABLE:
                    # Use webview 6.0+ API
                    webview.windows[0].load_html(self.html_content)
                else:
                    # Save to temp file and open in browser
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                        f.write(self.html_content)
                        temp_path = f.name
                    
                    webbrowser.open('file://' + temp_path)
                    print(f"Opened {xml_path} in browser: {temp_path}")
            else:
                self.show_error(f"Failed to parse XML file: {xml_path}")
        except Exception as e:
            self.show_error(f"Error loading file {xml_path}: {str(e)}")
            
            if self.html_content:
                # Create temporary HTML file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(self.html_content)
                    temp_html_path = f.name
                
                # Update window content
                if WEBVIEW_AVAILABLE:
                    webview.load_url(f'file://{temp_html_path}')
                else:
                    webbrowser.open(f'file://{temp_html_path}')
            else:
                self.show_error("Failed to parse XML file")
                
        except Exception as e:
            self.show_error(f"Error loading XML file: {str(e)}")
    
    def load_folder(self, folder_path):
        """Load folder and display XML files in sidebar"""
        try:
            self.current_folder = folder_path
            # Find all XML files in the folder
            self.xml_files_in_folder = []
            for file in os.listdir(folder_path):
                if file.lower().endswith('.xml'):
                    self.xml_files_in_folder.append(os.path.join(folder_path, file))
            
            # Sort files alphabetically
            self.xml_files_in_folder.sort(key=lambda x: os.path.basename(x).lower())
            
            # Generate HTML with file list and initial empty content
            self.html_content = self.generate_folder_view_html()
            
            if WEBVIEW_AVAILABLE:
                # Add menu to HTML content
                self.html_content = self.add_menu_to_html(self.html_content)
                webview.windows[0].load_html(self.html_content)
            else:
                # Save to temp file and open in browser
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(self.html_content)
                    temp_path = f.name
                
                webbrowser.open('file://' + temp_path)
                print(f"Opened folder view in browser: {temp_path}")
                
        except Exception as e:
            self.show_error(f"Error loading folder {folder_path}: {str(e)}")
    
    def load_xml_from_folder(self, xml_path):
        """Load XML file from folder view and update content area"""
        try:
            self.current_xml_path = xml_path
            
            # Generate the complete folder view HTML with the loaded XML content
            self.html_content = self.generate_folder_view_with_content(xml_path)
            
            if self.html_content and WEBVIEW_AVAILABLE:
                # Add menu to HTML content
                self.html_content = self.add_menu_to_html(self.html_content)
                # Load the complete HTML
                webview.windows[0].load_html(self.html_content)
                
                # Wait a moment for the DOM to load, then reinitialize overlay functionality
                def reinit_overlay():
                    try:
                        reinit_js = '''
                        // Reinitialize overlay functionality
                        setTimeout(function() {
                            if (typeof updateElementOverlay === 'function') {
                                updateElementOverlay();
                                console.log('Overlay functionality reinitialized');
                            } else {
                                console.warn('updateElementOverlay function not found');
                            }
                        }, 300);
                        '''
                        webview.windows[0].evaluate_js(reinit_js)
                    except Exception as e:
                        print(f"Warning: Could not reinitialize overlay: {e}")
                
                # Use a timer to execute after the HTML is loaded
                import threading
                timer = threading.Timer(0.5, reinit_overlay)
                timer.start()
            else:
                self.show_error(f"Failed to parse XML file: {xml_path}")
                
        except Exception as e:
            self.show_error(f"Error loading XML file from folder: {str(e)}")
    
    def get_xml_content_for_folder_view(self, xml_path):
        """Get only the content area HTML for a specific XML file without reloading the entire page"""
        try:
            # Update current XML path
            self.current_xml_path = xml_path
            
            # Generate the complete HTML content for the XML file
            xml_content_full = generate_html_content(xml_path)
            if xml_content_full:
                # Extract just the body content from the full HTML
                import re
                body_match = re.search(r'<body[^>]*>(.*?)</body>', xml_content_full, re.DOTALL)
                xml_body_content = body_match.group(1) if body_match else xml_content_full
                
                return xml_body_content
            else:
                return '<div class="empty-content"><h2>Error loading XML</h2><p>Failed to parse the selected file</p></div>'
                
        except Exception as e:
            return f'<div class="empty-content"><h2>Error</h2><p>Error loading XML file: {str(e)}</p></div>'
    
    def show_error(self, message):
        """Show error message"""
        if WEBVIEW_AVAILABLE:
            # Show error in webview context
            error_html = f'''
            <html>
            <body style="font-family: Arial; padding: 20px; text-align: center;">
                <h2 style="color: #e74c3c;">Error</h2>
                <p>{escape(message)}</p>
                <p><button onclick="window.location.reload()">Try Again</button></p>
            </body>
            </html>
            '''
            webview.load_html(error_html)
        else:
            print(f"Error: {message}")
    
    def generate_folder_view_html(self):
        """Generate HTML for folder view with file list and content area"""
        files_html = ""
        for xml_file in self.xml_files_in_folder:
            filename = os.path.basename(xml_file)
            files_html += f'''
                <div class="file-item" onclick="loadXmlFromList('{xml_file}')" 
                     title="{xml_file}">
                    📄 {filename}
                </div>
            '''
        
        if not files_html:
            files_html = '<div class="no-files">No XML files found in this folder</div>'
        
        return f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial; margin: 0; padding: 0; background: #f8f9fa; }}
                .container {{ display: flex; height: 100vh; }}
                .file-list {{ 
                    width: 300px; 
                    background: #e3f2fd; 
                    border-right: 1px solid #ccc; 
                    overflow-y: auto;
                    padding: 10px;
                }}
                .file-list h3 {{ 
                    margin: 0 0 15px 0; 
                    color: #2c3e50; 
                    font-size: 16px;
                    border-bottom: 2px solid #2980b9;
                    padding-bottom: 5px;
                }}
                .file-item {{ 
                    padding: 8px 12px; 
                    cursor: pointer; 
                    border-radius: 4px; 
                    margin: 2px 0;
                    transition: background 0.3s;
                }}
                .file-item:hover {{ 
                    background: #bbdefb; 
                }}
                .file-item.active {{ 
                    background: #2196f3; 
                    color: white; 
                }}
                .no-files {{ 
                    color: #666; 
                    font-style: italic; 
                    text-align: center; 
                    padding: 20px; 
                }}
                .content-area {{ 
                    flex: 1; 
                    padding: 20px; 
                    overflow: auto; 
                }}
                .status-bar {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: #34495e;
                    color: white;
                    padding: 8px 16px;
                    font-size: 12px;
                    border-top: 1px solid #2c3e50;
                }}
                .empty-content {{
                    text-align: center;
                    color: #666;
                    margin-top: 100px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="file-list">
                    <h3>📁 XML Files ({len(self.xml_files_in_folder)} files)</h3>
                    {files_html}
                </div>
                <div class="content-area" id="content-area">
                    <div class="empty-content">
                        <h2>Select an XML file</h2>
                        <p>Click on a file from the list to view its content</p>
                    </div>
                </div>
            </div>
            <div class="status-bar" id="status-bar">
                Folder: {self.current_folder} | No file selected
            </div>
            
            <script>
                function loadXmlFromList(filepath) {{
                    // Remove active class from all items
                    document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
                    
                    // Add active class to clicked item
                    event.target.classList.add('active');
                    
                    // Update status bar
                    document.getElementById('status-bar').textContent = 'Loading: ' + filepath + '...';
                    
                    // Call Python method to load the XML file
                    if (window.pywebview && window.pywebview.api) {{
                        window.pywebview.api.load_xml_from_folder(filepath);
                    }}
                }}
            </script>
        </body>
        </html>
        '''
    
    def get_welcome_html_with_simple_menu(self):
        """Generate welcome HTML"""
        return self.get_welcome_html()
    
    def generate_folder_view_with_content(self, xml_path):
        """Generate HTML for folder view with loaded XML content"""
        # Generate file list
        files_html = ""
        
        for xml_file in self.xml_files_in_folder:
            filename = os.path.basename(xml_file)
            active_class = "active" if xml_file == xml_path else ""
            files_html += f'''
                <div class="file-item {active_class}" onclick="loadXmlFromList('{xml_file}')" 
                     title="{xml_file}">
                    📄 {filename}
                </div>
            '''
        
        if not files_html:
            files_html = '<div class="no-files">No XML files found in this folder</div>'
        
        # Get the XML content body (without HTML wrapper)
        xml_content_full = generate_html_content(xml_path)
        if xml_content_full:
            # Extract just the body content from the full HTML
            import re
            body_match = re.search(r'<body[^>]*>(.*?)</body>', xml_content_full, re.DOTALL)
            xml_body_content = body_match.group(1) if body_match else xml_content_full
            
            # Extract the script content from the full HTML
            script_match = re.search(r'<script[^>]*>(.*?)</script>', xml_content_full, re.DOTALL)
            xml_scripts = script_match.group(1) if script_match else ""
        else:
            xml_body_content = '<div class="empty-content"><h2>Error loading XML</h2><p>Failed to parse the selected file</p></div>'
            xml_scripts = ""
        
        return f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial; margin: 0; padding: 0; background: #f8f9fa; }}
                .container {{ display: flex; height: 100vh; }}
                .file-list {{ 
                    width: 300px; 
                    background: #e3f2fd; 
                    border-right: 1px solid #ccc; 
                    overflow-y: auto;
                    padding: 10px;
                }}
                .file-list h3 {{ 
                    margin: 0 0 15px 0; 
                    color: #2c3e50; 
                    font-size: 16px;
                    border-bottom: 2px solid #2980b9;
                    padding-bottom: 5px;
                }}
                .file-item {{ 
                    padding: 8px 12px; 
                    cursor: pointer; 
                    border-radius: 4px; 
                    margin: 2px 0;
                    transition: background 0.3s;
                }}
                .file-item:hover {{ 
                    background: #bbdefb; 
                }}
                .file-item.active {{ 
                    background: #2196f3; 
                    color: white; 
                }}
                .no-files {{ 
                    color: #666; 
                    font-style: italic; 
                    text-align: center; 
                    padding: 20px; 
                }}
                .content-area {{ 
                    flex: 1; 
                    overflow: auto; 
                }}
                .status-bar {{
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: #34495e;
                    color: white;
                    padding: 8px 16px;
                    font-size: 12px;
                    border-top: 1px solid #2c3e50;
                }}
                
                /* XML Viewer Styles from generate_html_content */
                body{{font-family: Arial, Helvetica, sans-serif;}}
                .header{{padding:10px; background:#2c3e50; color:white; display:flex; align-items:center; gap:15px;}}
                .header h1{{margin:0; font-size:18px; color:white;}}
                .header-search-group{{display:flex; align-items:center; gap:10px;}}
                .header-search-group label{{font-size:12px; color:#ecf0f1; white-space:nowrap;}}
                .header-search-group input, .header-search-group select{{padding:4px; border:none; border-radius:3px; font-size:12px;}}
                .header-search-group .search-container{{position:relative;}}
                .header .clear-btn{{color:#666; background:white;}}
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
            </style>
        </head>
        <body>
            <div style="background: #f8f9fa; border-bottom: 1px solid #ddd; padding: 8px 15px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;">
                <div style="display: flex; gap: 20px; align-items: center;">
                    <span style="font-weight: 600; color: #2c3e50;">📁 Squish XML Viewer</span>
                    <div style="display: flex; gap: 15px;">
                        <label style="cursor: pointer; padding: 5px 10px; background: #3498db; color: white; border-radius: 3px; font-size: 13px;">
                            📄 Open File
                            <input type="file" accept=".xml" style="display: none;" onchange="handleFileOpen(this)">
                        </label>
                        <label style="cursor: pointer; padding: 5px 10px; background: #2ecc71; color: white; border-radius: 3px; font-size: 13px;">
                            📁 Open Folder
                            <input type="file" webkitdirectory style="display: none;" onchange="handleFolderOpen(this)">
                        </label>
                        <button onclick="showAbout()" style="cursor: pointer; padding: 5px 10px; background: #95a5a6; color: white; border: none; border-radius: 3px; font-size: 13px;">
                            ℹ️ About
                        </button>
                    </div>
                </div>
            </div>
            <div class="container">
                <div class="file-list">
                    <h3>📁 XML Files ({len(self.xml_files_in_folder)} files)</h3>
                    {files_html}
                </div>
                <div class="content-area" id="content-area">
                    {xml_body_content}
                </div>
            </div>
            <div class="status-bar" id="status-bar">
                Folder: {self.current_folder} | Current file: {xml_path}
            </div>
            
            <script>
                function loadXmlFromList(filepath) {{
                    // Remove active class from all items
                    document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
                    
                    // Add active class to clicked item
                    event.target.classList.add('active');
                    
                    // Update status bar
                    document.getElementById('status-bar').textContent = 'Loading: ' + filepath + '...';
                    
                    // Simple message - user will need to use native menus or keyboard shortcuts
                    alert('Please use File menu buttons above to open files. Direct file switching from list is disabled for stability.');
                }}
                
                // Menu functions for folder view
                function handleFileOpen(input) {{
                    if (input.files && input.files[0]) {{
                        const file = input.files[0];
                        if (file.name.toLowerCase().endsWith('.xml')) {{
                            alert('File selected: ' + file.name + '\\n\\nNote: Use keyboard shortcuts Ctrl+O for full functionality or restart the application with this file.');
                        }} else {{
                            alert('Please select an XML file.');
                        }}
                    }}
                }}
                
                function handleFolderOpen(input) {{
                    if (input.files && input.files.length > 0) {{
                        const xmlFiles = Array.from(input.files).filter(f => f.name.toLowerCase().endsWith('.xml'));
                        alert('Folder selected with ' + xmlFiles.length + ' XML files.\\n\\nNote: Use keyboard shortcuts Ctrl+Shift+O for full functionality or restart the application.');
                    }}
                }}
                
                function showAbout() {{
                    alert('Squish XML Viewer Desktop v1.0\\n\\nA desktop application for viewing and analyzing Squish XML snapshot files.\\n\\nFeatures:\\n- Interactive object tree navigation\\n- Property inspection\\n- Screenshot visualization with element overlay\\n- Search functionality\\n\\nBuilt with Python and pywebview.');
                }}
                
                // XML Viewer JavaScript from generate_html_content
                {xml_scripts}
                
                // Reinitialize overlay functionality after new content is loaded
                document.addEventListener('DOMContentLoaded', function() {{
                    // Reinitialize all tree item click handlers
                    setTimeout(function() {{
                        if (typeof updateElementOverlay === 'function') {{
                            updateElementOverlay();
                        }}
                        
                        // Re-attach click handlers to tree items
                        document.querySelectorAll('.tree-item[onclick]').forEach(function(item) {{
                            // The onclick attributes should already be in place from xml_scripts
                            // but we ensure overlay functions work
                        }});
                    }}, 100);
                }});
                
                // Also reinitialize when window is fully loaded
                window.addEventListener('load', function() {{
                    setTimeout(function() {{
                        if (typeof updateElementOverlay === 'function') {{
                            updateElementOverlay();
                        }}
                    }}, 200);
                }});
            </script>
        </body>
        </html>
        '''
    
    def show_about(self):
        """Show about dialog"""
        about_text = '''Squish XML Viewer Desktop v1.0

A desktop application for viewing and analyzing Squish XML snapshot files.

Features:
- Interactive object tree navigation
- Property inspection
- Screenshot visualization with element overlay
- Search functionality
- Context menus for copying data

Built with Python and pywebview.'''
        
        if WEBVIEW_AVAILABLE:
            # Show about as popup dialog using JavaScript
            about_js = f'''
            // Create modal overlay
            var modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 10000;
                display: flex;
                justify-content: center;
                align-items: center;
            `;
            
            // Create modal content
            var modalContent = document.createElement('div');
            modalContent.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 600px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                position: relative;
            `;
            
            modalContent.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #2c3e50;">About Squish XML Viewer</h2>
                    <button id="closeModal" style="
                        background: #e74c3c;
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        cursor: pointer;
                        font-size: 18px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    ">×</button>
                </div>
                <div style="color: #34495e; line-height: 1.6;">
                    <p><strong>Version:</strong> Desktop Edition</p>
                    <p><strong>Description:</strong> A desktop application for viewing and analyzing Squish XML snapshot files.</p>
                    <br>
                    <p><strong>Features:</strong></p>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Interactive object tree navigation</li>
                        <li>Property inspection</li>
                        <li>Screenshot visualization with element overlay</li>
                        <li>Search functionality</li>
                        <li>Context menus for copying data</li>
                        <li>Recent files management (LRU)</li>
                        <li>Drag & drop support</li>
                        <li>Native file dialogs</li>
                    </ul>
                    <br>
                    <p><strong>Technology:</strong> Built with Python and pywebview</p>
                    <p><strong>Author:</strong> XML Viewer Team</p>
                </div>
                <div style="text-align: center; margin-top: 30px;">
                    <button id="okButton" style="
                        background: #3498db;
                        color: white;
                        border: none;
                        padding: 10px 30px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 16px;
                    ">OK</button>
                </div>
            `;
            
            modal.appendChild(modalContent);
            document.body.appendChild(modal);
            
            // Close modal handlers
            function closeModal() {{
                document.body.removeChild(modal);
            }}
            
            document.getElementById('closeModal').onclick = closeModal;
            document.getElementById('okButton').onclick = closeModal;
            
            // Close on overlay click
            modal.onclick = function(e) {{
                if (e.target === modal) {{
                    closeModal();
                }}
            }};
            
            // Close on Escape key
            document.addEventListener('keydown', function escapeHandler(e) {{
                if (e.key === 'Escape') {{
                    closeModal();
                    document.removeEventListener('keydown', escapeHandler);
                }}
            }});
            '''
            
            # Execute JavaScript to show popup
            webview.windows[0].evaluate_js(about_js)
        else:
            print(about_text)
    
    def exit_app(self):
        """Exit the application"""
        if WEBVIEW_AVAILABLE:
            webview.windows[0].destroy()
        else:
            sys.exit(0)
    
    def run(self, xml_path=None):
        """Run the desktop application"""
        if not WEBVIEW_AVAILABLE:
            print("Warning: pywebview not available. Starting in browser mode...")
            if xml_path:
                self.load_xml_file(xml_path)
            else:
                self.open_file_dialog()
            return
        
        # Create initial content
        if xml_path and os.path.isfile(xml_path):
            initial_html = generate_html_content(xml_path)
            self.current_xml_path = xml_path
            # Add simple HTML menu without JavaScript callbacks
            initial_html = initial_html
        else:
            # Show welcome screen using the reusable method
            initial_html = self.get_welcome_html_with_simple_menu()
        
        # Store reference to app instance
        app = self
        
        # Create menu items using native pywebview menus
        menu_items = [
            {
                'label': 'File',
                'submenu': [
                    {
                        'label': 'Open XML Snapshot',
                        'function': app.open_file_dialog
                    },
                    {
                        'type': 'separator'
                    },
                    {
                        'label': 'Close',
                        'function': app.close_file
                    },
                    {
                        'type': 'separator'
                    },
                    {
                        'label': 'Exit',
                        'function': app.exit_app
                    }
                ]
            },
            {
                'label': 'Help',
                'submenu': [
                    {
                        'label': 'About',
                        'function': app.show_about
                    }
                ]
            }
        ]
        
        # Create webview window without problematic menu for now
        window = webview.create_window(
            'Squish XML Viewer',
            html=initial_html,
            width=1400,
            height=900,
            min_size=(800, 600),
            js_api=app  # Enable JS API for mouse events
        )
        
        # Start the application
        webview.start(debug=False)

def main():
    """Main function"""
    app = SquishXMLViewerDesktop()
    
    # Check command line arguments
    xml_path = None
    if len(sys.argv) > 1:
        xml_path = sys.argv[1]
        if not os.path.isfile(xml_path):
            print(f"XML file not found: {xml_path}")
            xml_path = None
    
    # Run the application
    app.run(xml_path)

if __name__ == "__main__":
    main()