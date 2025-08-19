#!/usr/bin/env python3
"""
VxLAN Tunnel Management System
Main entry point for both CLI and API services
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from vxlan_manager.cli import cli
from vxlan_manager.api import create_app
from vxlan_manager.logger import setup_logging
from vxlan_manager.config import load_app_config

def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Load application configuration
    config = load_app_config()
    
    # Check if running as API service
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # Run API service
        import uvicorn
        app = create_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            log_level="info"
        )
    elif len(sys.argv) > 1 and sys.argv[1] == "service":
        # Run as systemd service (API mode)
        import uvicorn
        app = create_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5000,
            log_level="info"
        )
    else:
        # Run CLI interface
        cli()

if __name__ == "__main__":
    main()
