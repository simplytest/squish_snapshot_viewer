#!/usr/bin/env python3
"""
Debug script to check if overlay functions are included in folder view HTML
"""

import os
import sys
from squish_xml_viewer_desktop import SquishXMLViewerDesktop, generate_html_content

def debug_overlay_in_folder_view():
    """Debug overlay functionality in folder view"""
    print("=== DEBUG: Overlay in Folder View ===")
    
    # Test file
    xml_file = "squishsnapshot.xml"
    if not os.path.exists(xml_file):
        print(f"❌ XML file not found: {xml_file}")
        return
    
    print(f"✓ XML file found: {xml_file}")
    
    # Create app and set up folder view
    app = SquishXMLViewerDesktop()
    app.current_folder = os.path.dirname(os.path.abspath(xml_file))
    app.xml_files_in_folder = [xml_file]
    
    print(f"✓ App initialized")
    print(f"✓ Current folder: {app.current_folder}")
    print(f"✓ XML files: {app.xml_files_in_folder}")
    
    # Check 1: Regular generate_html_content
    print("\n--- Checking regular generate_html_content ---")
    regular_html = generate_html_content(xml_file)
    if regular_html:
        overlay_functions = ["updateElementOverlay", "drawElementOverlay", "element-overlay"]
        for func in overlay_functions:
            if func in regular_html:
                print(f"✓ Regular HTML contains: {func}")
            else:
                print(f"❌ Regular HTML missing: {func}")
    
    # Check 2: Folder view generate_folder_view_with_content
    print("\n--- Checking folder view HTML ---")
    try:
        folder_html = app.generate_folder_view_with_content(xml_file)
        if folder_html:
            overlay_functions = ["updateElementOverlay", "drawElementOverlay", "element-overlay"]
            for func in overlay_functions:
                if func in folder_html:
                    print(f"✓ Folder HTML contains: {func}")
                else:
                    print(f"❌ Folder HTML missing: {func}")
            
            # Count script tags
            script_count = folder_html.count('<script')
            print(f"📊 Script tags in folder HTML: {script_count}")
            
            # Check if click handlers are present
            if 'onclick=' in folder_html:
                print(f"✓ Click handlers found in folder HTML")
                # Count onclick handlers
                onclick_count = folder_html.count('onclick=')
                print(f"📊 onclick handlers: {onclick_count}")
            else:
                print(f"❌ No click handlers in folder HTML")
                
        else:
            print("❌ Failed to generate folder HTML")
    except Exception as e:
        print(f"❌ Error generating folder HTML: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 3: New method get_xml_content_for_folder_view
    print("\n--- Checking get_xml_content_for_folder_view ---")
    try:
        content_html = app.get_xml_content_for_folder_view(xml_file)
        if content_html:
            overlay_functions = ["updateElementOverlay", "drawElementOverlay", "element-overlay"]
            for func in overlay_functions:
                if func in content_html:
                    print(f"✓ Content HTML contains: {func}")
                else:
                    print(f"❌ Content HTML missing: {func}")
        else:
            print("❌ Failed to generate content HTML")
    except Exception as e:
        print(f"❌ Error generating content HTML: {e}")

if __name__ == "__main__":
    debug_overlay_in_folder_view()