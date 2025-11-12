#!/usr/bin/env python3
"""
Torrent Search Engine - Startup Script
Easy launcher for the torrent search engine application
"""

import sys
import os
import subprocess
import webbrowser
import time
from threading import Timer

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import requests
        import bs4
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_tor():
    """Check if Tor is available for onion sites"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()
        
        if result == 0:
            print("✓ Tor is running on port 9050 - Onion sites available")
            return True
        else:
            print("⚠ Tor is not running - Onion sites will not be available")
            print("  To enable onion sites, install and start Tor:")
            print("  - Download Tor Browser from https://www.torproject.org")
            print("  - Or install Tor service and start it")
            return False
    except Exception as e:
        print(f"⚠ Could not check Tor status: {e}")
        return False

def open_browser():
    """Open web browser after a short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def main():
    print("🔍 Torrent Search Engine - Starting up...")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check Tor (optional)
    check_tor()
    
    print("\n🚀 Starting web server...")
    print("📱 The application will open in your web browser")
    print("🌐 If it doesn't open automatically, visit: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser in a separate thread
    Timer(2.0, open_browser).start()
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()