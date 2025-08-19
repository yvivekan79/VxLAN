
#!/usr/bin/env python3
"""
Example: Deploy Site A to Site B VxLAN tunnel using orchestrator
"""

import asyncio
import sys
import os

# Add parent directory to path to import vxlan_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vxlan_manager.orchestrator import VxLANOrchestrator, RemoteNode
from vxlan_manager.core import VxLANTunnel

async def deploy_site_a_site_b_tunnel():
    """Deploy VxLAN tunnel between Site A and Site B"""
    
    # Initialize orchestrator
    orchestrator = VxLANOrchestrator()
    
    # Add Site A node (SSH connection)
    site_a = RemoteNode(
        node_id="site-a",
        hostname="203.0.113.10",
        connection_type="ssh",
        port=22,
        username="admin",
        ssh_key_path="~/.ssh/cpe_key"
    )
    
    # Add Site B node (HTTP API connection)
    site_b = RemoteNode(
        node_id="site-b", 
        hostname="198.51.100.20",
        connection_type="http",
        port=5001,
        api_token="your-api-token-here"
    )
    
    orchestrator.add_node(site_a)
    orchestrator.add_node(site_b)
    
    # Create tunnel configuration for Site A
    site_a_tunnel = VxLANTunnel(
        vni=1001,
        local_ip="203.0.113.10",
        remote_ip="198.51.100.20", 
        interface_name="vxlan1001",
        bridge_name="br-lan",
        physical_interface="eth0",
        mtu=1450,
        port=4789,
        label="site-a-to-site-b"
    )
    
    # Create tunnel configuration for Site B
    site_b_tunnel = VxLANTunnel(
        vni=1001,
        local_ip="198.51.100.20",
        remote_ip="203.0.113.10",
        interface_name="vxlan1001", 
        bridge_name="br-lan",
        physical_interface="eth0",
        mtu=1450,
        port=4789,
        label="site-b-to-site-a"
    )
    
    print("Deploying VxLAN tunnel between Site A and Site B...")
    
    try:
        # Deploy tunnel on Site A
        print("Creating tunnel on Site A...")
        site_a_result = await orchestrator.create_tunnel_on_node("site-a", site_a_tunnel)
        print(f"Site A result: {site_a_result}")
        
        # Deploy tunnel on Site B  
        print("Creating tunnel on Site B...")
        site_b_result = await orchestrator.create_tunnel_on_node("site-b", site_b_tunnel)
        print(f"Site B result: {site_b_result}")
        
        print("✅ VxLAN tunnel deployment completed successfully!")
        
        # Verify tunnel status
        print("\nVerifying tunnel status...")
        site_a_status = await orchestrator.get_node_status("site-a")
        site_b_status = await orchestrator.get_node_status("site-b")
        
        print(f"Site A status: {site_a_status}")
        print(f"Site B status: {site_b_status}")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Run the deployment
    success = asyncio.run(deploy_site_a_site_b_tunnel())
    if success:
        print("\n🎉 Site A to Site B VxLAN tunnel is now active!")
        print("Both sites can now communicate over the secure overlay network.")
    else:
        print("\n💥 Deployment failed. Check the logs for details.")
