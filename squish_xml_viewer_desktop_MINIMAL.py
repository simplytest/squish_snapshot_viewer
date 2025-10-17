#!/usr/bin/env python3
"""
squish_xml_viewer_desktop.py

EINFACHE Desktop-Version des Squish XML Viewers.
Verwendet die funktionierende Browser-Version als Basis.

Usage:
    python3 squish_xml_viewer_desktop.py path/to/snapshot.xml
"""

import sys
import os
import subprocess

# Try to import webview
try:
    import webview
    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    print("pywebview not available, falling back to browser mode")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 squish_xml_viewer_desktop.py path/to/file.xml")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    if not os.path.isfile(xml_path):
        print("XML file not found:", xml_path)
        sys.exit(2)
    
    if WEBVIEW_AVAILABLE:
        # Desktop mode: Generate HTML and show in webview
        try:
            # Use the working browser version to generate HTML
            result = subprocess.run([
                sys.executable, 'squish_xml_viewer.py', xml_path
            ], cwd=os.path.dirname(os.path.abspath(__file__)), 
               capture_output=True, text=True)
            
            if result.returncode != 0:
                print("Error generating HTML:", result.stderr)
                sys.exit(3)
            
            # Find the generated HTML file
            html_path = os.path.splitext(xml_path)[0] + "_viewer.html"
            if not os.path.exists(html_path):
                print("Generated HTML file not found:", html_path)
                sys.exit(4)
            
            # Read the HTML content
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Create webview window
            window = webview.create_window(
                f'Squish XML Viewer - {os.path.basename(xml_path)}',
                html=html_content,
                width=1400,
                height=900,
                min_size=(800, 600)
            )
            
            # Start the application
            webview.start(debug=False)
            
        except Exception as e:
            print(f"Desktop mode failed: {e}")
            print("Falling back to browser mode...")
            # Fallback to browser mode
            subprocess.run([sys.executable, 'squish_xml_viewer.py', xml_path])
    else:
        # Browser mode fallback
        subprocess.run([sys.executable, 'squish_xml_viewer.py', xml_path])

if __name__ == "__main__":
    main()