function filterTreeByPropertyValue() {
    var searchTerm = document.getElementById('propertyValueSearch').value.toLowerCase();
    var treeContainer = document.getElementById('treeContainer');
    var allNodes = treeContainer.querySelectorAll('li');

    // First, remove all highlighting
    var allSpans = treeContainer.querySelectorAll('.node');
    allSpans.forEach(function(span) {
        span.style.backgroundColor = '';
    });

    if (searchTerm === '') {
        allNodes.forEach(function(node) {
            node.style.display = '';
        });
        var allUls = treeContainer.querySelectorAll('ul');
        allUls.forEach(function(ul) {
            ul.style.display = '';
        });
        return;
    }
    // Hide all nodes first
    allNodes.forEach(function(node) {
        node.style.display = 'none';
    });
    // Show nodes where any property value matches
    var nodeSpans = treeContainer.querySelectorAll('.node');
    nodeSpans.forEach(function(span) {
        var props = span.getAttribute('data-props') || '{}';
        try {
            var textarea = document.createElement('textarea');
            textarea.innerHTML = props;
            var propsObj = eval('(' + textarea.value + ')');
            var found = false;
            for (var key in propsObj) {
                if (propsObj.hasOwnProperty(key)) {
                    var value = propsObj[key];
                    if (typeof value === 'string' && value.toLowerCase().includes(searchTerm)) {
                        found = true;
                        break;
                    }
                }
            }
            if (found) {
                span.style.backgroundColor = 'yellow';
                // Show this node and all its parents
                var current = span.closest('li');
                while (current) {
                    current.style.display = '';
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
        } catch(e) {}
    });
}

function clearPropertyValueSearch() {
    var input = document.getElementById('propertyValueSearch');
    input.value = '';
    input.focus();
    filterTreeByPropertyValue();
    toggleClearButton('propertyValueSearch', 'clearPropertyValueSearch');
}
// squish_xml_viewer.js - JavaScript functionality for the XML viewer

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\/]/g, '\$&'); // $& means the whole matched string
}

function highlightText(text, searchTerms) {
    if (!searchTerms || searchTerms.length === 0) {
        return text;
    }
    // remove empty strings
    searchTerms = searchTerms.filter(Boolean);
    if (searchTerms.length === 0) {
        return text;
    }
    var combinedRegex = searchTerms.map(term => '(' + escapeRegExp(term) + ')').join('|');
    var regex = new RegExp(combinedRegex, 'gi');
    return text.toString().replace(regex, '<mark>$&</mark>');
}

function formatPropertiesAsTable(propsStr, searchTerm, highlightTerms) {
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
                var highlightedKey = highlightText(key, highlightTerms);
                var highlightedValue = highlightText(value, highlightTerms);
                table += "<tr><td>" + highlightedKey + "</td><td>" + highlightedValue + "</td></tr>";
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
                    var highlightedDisplayName = highlightText(displayName, highlightTerms);
                    var highlightedValue = highlightText(value, highlightTerms);
                    groupContent += "<tr class='group-item'><td>&nbsp;&nbsp;&nbsp;&nbsp;" + highlightedDisplayName + "</td><td>" + highlightedValue + "</td></tr>";
                    groupHasMatches = true;
                }
            }
            
            // Only add group if it has matches
            if (groupHasMatches) {
                var highlightedGroupName = highlightText(groupName, highlightTerms);
                table += "<tr class='group-header'><td colspan='2'><strong>" + highlightedGroupName + "</strong></td></tr>";
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

// Global variables
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
    
    // Get actual displayed image dimensions
    var imgRect = screenshotImg.getBoundingClientRect();
    var containerRect = container.getBoundingClientRect();
    
    // Calculate scale factor between actual image and displayed image
    var scaleX = imgRect.width / screenshotImg.naturalWidth;
    var scaleY = imgRect.height / screenshotImg.naturalHeight;
    
    var offsetX = imgRect.left - containerRect.left;
    var offsetY = imgRect.top - containerRect.top;

    // Calculate overlay position and size
    var overlayX = (x * scaleX) + offsetX - 2; // 2px left
    var overlayY = (y * scaleY) + offsetY - 2; // 2px up
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
    
    var propsSearchTerm = document.getElementById('propsSearch').value.toLowerCase();
    var propertyValueSearchTerm = document.getElementById('propertyValueSearch').value.toLowerCase();

    var highlightTerms = [];
    if (propsSearchTerm) highlightTerms.push(propsSearchTerm);
    if (propertyValueSearchTerm) highlightTerms.push(propertyValueSearchTerm);

    var html = formatPropertiesAsTable(currentPropsData, propsSearchTerm, highlightTerms);
    document.getElementById("props").innerHTML = html;
}

function filterTree(nodesToDisplay = null) {
    console.log("filterTree called with nodesToDisplay:", nodesToDisplay);
    var searchTerm = document.getElementById('treeSearch').value.toLowerCase();
    var treeContainer = document.getElementById('treeContainer');
    var showOnlyMatchesChecked = document.getElementById('showOnlyMatches').checked;
    console.log("showOnlyMatchesChecked:", showOnlyMatchesChecked);

    // First, remove all highlighting
    var allSpans = treeContainer.querySelectorAll('.node');
    allSpans.forEach(function(span) {
        span.style.backgroundColor = '';
    });

    // Reset all nodes to visible initially
    var allNodes = treeContainer.querySelectorAll('li');
    console.log("Total li nodes:", allNodes.length);
    allNodes.forEach(function(node) {
        node.style.display = '';
    });
    var allUls = treeContainer.querySelectorAll('ul');
    allUls.forEach(function(ul) {
        ul.style.display = '';
    });

    // Determine the set of nodes to consider for display
    var nodesToProcess = [];
    if (nodesToDisplay && nodesToDisplay.length > 0) {
        // If specific nodes are provided (e.g., from screenshot click)
        nodesToProcess = nodesToDisplay;
    } else if (searchTerm !== '') {
        // If text search term is present
        var nodeSpans = treeContainer.querySelectorAll('.node');
        nodeSpans.forEach(function(span) {
            if (span.textContent.toLowerCase().includes(searchTerm)) {
                nodesToProcess.push(span);
            }
        });
    } else {
        // No specific nodes and no search term, so all nodes should remain visible (already reset above)
        console.log("No nodes to process, returning.");
        return;
    }
    console.log("nodesToProcess:", nodesToProcess);

    // Apply filtering based on showOnlyMatchesChecked
    if (showOnlyMatchesChecked && (nodesToProcess.length > 0 || searchTerm !== '')) {
        console.log("showOnlyMatchesChecked is true, hiding all nodes.");
        // If showOnlyMatches is checked and there are nodes to process or a search term,
        // hide all nodes first, then show only the matching ones and their parents.
        allNodes.forEach(function(node) {
            node.style.display = 'none';
        });
    }

    // Show the nodes that match the criteria and their parents
    nodesToProcess.forEach(function(nodeSpan) {
        nodeSpan.style.backgroundColor = 'yellow'; // Highlight the node
        var current = nodeSpan.closest('li');
        while (current) {
            current.style.display = '';
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
    });
}

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

// Context menu functions
function copyToClipboard(type) {
    // Check if the clicked item is disabled
    var contextMenuItem = event.target.closest('.context-menu-item');
    if (contextMenuItem && contextMenuItem.classList.contains('disabled-menu-item')) {
        return; // Do nothing if disabled
    }

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
    } else if (type === 'copy-as-object') {
        what = "object";
        if (currentContextNode) {
            var props = currentContextNode.getAttribute("data-props") || "{}";
            try {
                var textarea = document.createElement('textarea');
                textarea.innerHTML = props;
                var decodedStr = textarea.value;
                var propsObj = eval("(" + decodedStr + ")");

                var objectName = propsObj['objectName'];
                var namePart = objectName ? `"${objectName}"` : "None";
                var simplifiedType = propsObj['simplifiedType'] || '';
                
                var extraProps = {};
                var realnameAttrs = {};
                // Parse realname and merge attributes
                if (propsObj['realname']) {
                    realnameAttrs = parseRealnameAttributes(propsObj['realname'], attributeWhitelist);
                    extraProps = Object.assign(extraProps, realnameAttrs);
                }

                // Add whitelisted properties from propsObj if not already in realname
                for (var key in propsObj) {
                    if (attributeWhitelist.includes(key) && propsObj[key] !== '' && !realnameAttrs.hasOwnProperty(key)) {
                        extraProps[key] = propsObj[key];
                    }
                }

                var extraPropsString = Object.entries(extraProps).map(([key, value]) => `"${key}": "${value}"`).join(', ');

                textToCopy = `BasePage.element(BasePage.quick_view, ${namePart}, "${simplifiedType}"`;
                if (extraPropsString) {
                    textToCopy += ` , **{${extraPropsString}}`;
                }
                textToCopy += `)`;

            } catch(e) {
                textToCopy = "Failed to generate object string";
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

    // New logic for "copy as object"
    var props = currentContextNode.getAttribute("data-props") || "{}";
    try {
        var textarea = document.createElement('textarea');
        textarea.innerHTML = props;
        var decodedStr = textarea.value;
        var propsObj = eval("(" + decodedStr + ")");
        var realname = propsObj['realname'] || "";

        var copyAsObjectItem = document.querySelector('[data-type="copy-as-object"]');
        var braceCount = (realname.match(/{/g) || []).length;

        if (braceCount <= 1 || (braceCount === 2 && realname.includes("type='QuickView'"))) {
            copyAsObjectItem.classList.remove('disabled-menu-item');
        } else {
            copyAsObjectItem.classList.add('disabled-menu-item');
        }
    } catch(e) {
        var copyAsObjectItem = document.querySelector('[data-type="copy-as-object"]');
        copyAsObjectItem.classList.add('disabled-menu-item');
    }

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

// Helper function to parse attributes from realname string
function parseRealnameAttributes(realnameString, whitelist) {
    var attributes = {};
    whitelist.forEach(function(key) {
        var regex = new RegExp(key + "='([^']*)'");
        var match = realnameString.match(regex);
        if (match) {
            attributes[key] = match[1];
        }
    });
    return attributes;
}

function findElementsByCoordinates(x, y) {
    var screenshotImg = document.querySelector('.screenshot');
    if (!screenshotImg) return;

    if (!screenshotGeometry) {
        // Try to find screenshot geometry from the first element with geometry
        var allNodes = document.querySelectorAll('.node');
        for (var i = 0; i < allNodes.length; i++) {
            var nodeProps = allNodes[i].getAttribute("data-props") || "{}";
            try {
                var nodeTextarea = document.createElement('textarea');
                nodeTextarea.innerHTML = nodeProps;
                var nodeDecoded = nodeTextarea.value;
                var nodePropsObj = JSON.parse(nodeDecoded);
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

    var scaleX = screenshotImg.naturalWidth / screenshotImg.width;
    var scaleY = screenshotImg.naturalHeight / screenshotImg.height;

    var clickX = (x * scaleX) + screenshotGeometry.x;
    var clickY = (y * scaleY) + screenshotGeometry.y;

    var allNodes = document.querySelectorAll('.node');
    allNodes.forEach(function(node) {
        node.classList.remove('highlight');
    });

    var matchingNodes = [];
    allNodes.forEach(function(node) {
        var props = node.getAttribute('data-props') || '{}';
        try {
            var textarea = document.createElement('textarea');
            textarea.innerHTML = props;
            var propsObj = JSON.parse(textarea.value);

            var elemX = parseInt(propsObj['geometry_x']);
            var elemY = parseInt(propsObj['geometry_y']);
            var elemWidth = parseInt(propsObj['geometry_width']);
            var elemHeight = parseInt(propsObj['geometry_height']);

            if (!isNaN(elemX) && !isNaN(elemY) && !isNaN(elemWidth) && !isNaN(elemHeight)) {
                if (clickX >= elemX && clickX <= elemX + elemWidth &&
                    clickY >= elemY && clickY <= elemY + elemHeight) {
                    matchingNodes.push({node: node, width: elemWidth, height: elemHeight});
                }
            }
        } catch (e) {}
    });

    if (matchingNodes.length > 0) {
        // Find the node with the smallest area
        var smallestNode = matchingNodes.reduce(function(prev, curr) {
            var prevArea = prev.width * prev.height;
            var currArea = curr.width * curr.height;
            return (prevArea < currArea) ? prev : curr;
        });

        // Select the smallest node and update overlay
        document.querySelectorAll(".node").forEach(n => n.classList.remove("selected"));
        smallestNode.node.classList.add("selected");
        currentSelectedNode = smallestNode.node;
        var props = currentSelectedNode.getAttribute("data-props") || "{}";
        currentPropsData = props;
        filterAndDisplayProperties();
        updateElementOverlay(); // Explicitly redraw the overlay for the newly selected node

        // Also highlight all matching nodes in the tree
        matchingNodes.forEach(function(match) {
            match.node.classList.add('highlight');
        });
        filterTree(matchingNodes.map(m => m.node)); // Call filterTree with the matching nodes
    } else {
        filterTree([]); // If no nodes match, ensure the tree is reset (all visible if checkbox is off)
    }
}

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
    originalTreeHTML = document.getElementById('treeContainer').innerHTML;

    // Property Value Search
    var propertyValueSearch = document.getElementById('propertyValueSearch');
    if (propertyValueSearch) {
        propertyValueSearch.addEventListener('input', function() {
            filterTreeByPropertyValue();
            toggleClearButton('propertyValueSearch', 'clearPropertyValueSearch');
        });
    }
    
    // Add search functionality
    document.getElementById("treeSearch").addEventListener("input", function() {
        filterTree();
        toggleClearButton('treeSearch', 'clearTreeSearch');
        // Wenn Property-Value-Suche aktiv, Tree-Suche ignorieren
        if (propertyValueSearch && propertyValueSearch.value.length > 0) {
            filterTreeByPropertyValue();
        }
    });
    document.getElementById("propsSearch").addEventListener("input", function() {
        filterAndDisplayProperties();
        toggleClearButton('propsSearch', 'clearPropsSearch');
    });

    // Add event listener for showOnlyMatches checkbox
    var showOnlyMatchesCheckbox = document.getElementById('showOnlyMatches');
    if (showOnlyMatchesCheckbox) {
        showOnlyMatchesCheckbox.addEventListener('change', function() {
            filterTree();
        });
    }

    // Screenshot click handler
    var screenshotContainer = document.getElementById('screenshotContainer');
    if (screenshotContainer) {
        screenshotContainer.addEventListener('click', function(e) {
            var screenshotImg = document.querySelector('.screenshot');
            if (!screenshotImg) return;

            var rect = screenshotImg.getBoundingClientRect();
            var x = e.clientX - rect.left;
            var y = e.clientY - rect.top;

            findElementsByCoordinates(x, y);
        });
    }

    // Clear Highlight button
    var clearHighlightButton = document.getElementById('clearHighlight');
    if (clearHighlightButton) {
        clearHighlightButton.addEventListener('click', function() {
            var allNodes = document.querySelectorAll('.node');
            allNodes.forEach(function(node) {
                node.classList.remove('highlight');
            });
            clearHighlightButton.style.display = 'none';
        });
    }

    // Consolidated click handler
    document.addEventListener('click', function(e) {
        // Node selection
        if (e.target.classList.contains("node")) {
            document.querySelectorAll(".node").forEach(n => n.classList.remove("selected"));
            e.target.classList.add("selected");
            currentSelectedNode = e.target;
            var props = e.target.getAttribute("data-props") || "{}";
            currentPropsData = props;
            filterAndDisplayProperties();
            updateElementOverlay();
        }

        // Context menu item click
        var contextMenuItem = e.target.closest('.context-menu-item');
        if (contextMenuItem) {
            const type = contextMenuItem.getAttribute('data-type');
            if (type) {
                copyToClipboard(type);
            }
        } else if (!e.target.closest('.context-menu')) {
            hideContextMenus();
        }

        // Toggle tree nodes
        if (e.target.classList.contains('toggle')) {
            var nested = e.target.parentElement.querySelector('.nested');
            if (nested) {
                nested.classList.toggle('collapsed');
                e.target.textContent = nested.classList.contains('collapsed') ? '+' : '-';
            }
        }
    });

    // Context menu handler
    document.addEventListener('contextmenu', function(e) {
        if (e.target.classList.contains('node')) {
            showTreeContextMenu(e, e.target);
        } else {
            var targetCell = e.target.closest('.props-table td');
            if (targetCell) {
                var row = targetCell.parentElement;
                if (row.cells.length === 2) {
                    var propName = row.cells[0].textContent.trim();
                    var propValue = row.cells[1].textContent.trim();
                    showPropsContextMenu(e, propName, propValue);
                }
            }
        }
    });
});