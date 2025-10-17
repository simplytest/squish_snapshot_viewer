#!/usr/bin/env python3
"""
Simple test to check overlay functionality with pywebview
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from squish_xml_viewer_desktop import SquishXMLViewerDesktop

def test_simple_xml_viewer():
    """Test the XML viewer with simple single file"""
    print("=== Simple XML Viewer Test ===")
    
    xml_file = "squishsnapshot.xml"
    if not os.path.exists(xml_file):
        print(f"❌ XML file not found: {xml_file}")
        return
    
    print(f"✓ XML file found: {xml_file}")
    
    try:
        app = SquishXMLViewerDesktop()
        print("✓ App created")
        
        # Start with simple file (should work with overlay)
        print("Starting app with single XML file...")
        app.run(xml_file)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_xml_viewer()