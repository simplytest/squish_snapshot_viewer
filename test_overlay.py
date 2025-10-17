#!/usr/bin/env python3
"""
Test script to verify overlay functionality in the desktop XML viewer
"""

import sys
import os
from squish_xml_viewer_desktop import SquishXMLViewerDesktop, generate_html_content

def test_overlay_functionality():
    """Test if overlay functions are properly included in generated HTML"""
    print("Testing Overlay Functionality...")
    print("=" * 50)
    
    # Test 1: Check if generate_html_content includes overlay functions
    xml_file = "squishsnapshot.xml"
    if not os.path.exists(xml_file):
        print(f"❌ XML file not found: {xml_file}")
        return False
    
    print(f"✓ XML file found: {xml_file}")
    
    # Generate HTML content
    try:
        html_content = generate_html_content(xml_file)
        if not html_content:
            print("❌ Failed to generate HTML content")
            return False
        print("✓ HTML content generated successfully")
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        return False
    
    # Test 2: Check for overlay functions in HTML
    overlay_functions = [
        "updateElementOverlay",
        "drawElementOverlay", 
        "element-overlay"
    ]
    
    missing_functions = []
    for func in overlay_functions:
        if func in html_content:
            print(f"✓ Found: {func}")
        else:
            print(f"❌ Missing: {func}")
            missing_functions.append(func)
    
    # Test 3: Test desktop app initialization
    try:
        app = SquishXMLViewerDesktop()
        print("✓ Desktop app initialized successfully")
        
        # Test folder view generation if the method exists
        if hasattr(app, 'generate_folder_view_with_content'):
            try:
                app.current_folder = os.path.dirname(os.path.abspath(xml_file))
                app.xml_files_in_folder = [xml_file]
                folder_html = app.generate_folder_view_with_content(xml_file)
                
                folder_missing = []
                for func in overlay_functions:
                    if func in folder_html:
                        print(f"✓ Folder view contains: {func}")
                    else:
                        print(f"❌ Folder view missing: {func}")
                        folder_missing.append(func)
                
                if not folder_missing:
                    print("✅ All overlay functions found in folder view!")
                else:
                    print(f"❌ Folder view missing: {folder_missing}")
                    
            except Exception as e:
                print(f"❌ Error testing folder view: {e}")
        else:
            print("❌ generate_folder_view_with_content method not found")
            
    except Exception as e:
        print(f"❌ Error initializing desktop app: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 50)
    if not missing_functions:
        print("🎉 SUCCESS: All overlay functions are properly included!")
        return True
    else:
        print(f"❌ FAILED: Missing functions: {missing_functions}")
        return False

if __name__ == "__main__":
    success = test_overlay_functionality()
    sys.exit(0 if success else 1)