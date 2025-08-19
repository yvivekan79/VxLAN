
#!/usr/bin/env python3
"""
VxLAN Agent - Lightweight service for remote tunnel management
"""

import sys
import argparse
from pathlib import Path

# Add project directory to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from vxlan_manager.agent import create_agent_app
from vxlan_manager.logger import setup_logging

def main():
    parser = argparse.ArgumentParser(description='VxLAN Agent')
    parser.add_argument('--node-id', help='Node identifier')
    parser.add_argument('--host', default='0.0.0.0', help='Bind host')
    parser.add_argument('--port', type=int, default=5001, help='Bind port')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Create and run agent
    app = create_agent_app(args.node_id)
    
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
