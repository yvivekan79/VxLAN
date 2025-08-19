
"""
Orchestrator for managing VxLAN tunnels across multiple remote servers
"""

import asyncio
import json
import aiohttp
import asyncssh
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from .core import VxLANTunnel
from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class RemoteNode:
    """Remote node configuration"""
    node_id: str
    hostname: str
    connection_type: str  # 'ssh' or 'http'
    port: int
    username: Optional[str] = None
    ssh_key_path: Optional[str] = None
    api_token: Optional[str] = None
    
class VxLANOrchestrator:
    """Orchestrator for managing remote VxLAN agents"""
    
    def __init__(self, config_path: str = "./config/nodes.yaml"):
        self.config_path = Path(config_path)
        self.nodes: Dict[str, RemoteNode] = {}
        self.load_node_configuration()
    
    def load_node_configuration(self):
        """Load remote node configuration"""
        try:
            if self.config_path.exists():
                import yaml
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                for node_id, node_data in data.get('nodes', {}).items():
                    node = RemoteNode(**node_data)
                    self.nodes[node_id] = node
                    logger.info(f"Loaded node configuration: {node_id}")
        except Exception as e:
            logger.error(f"Failed to load node configuration: {e}")
    
    async def execute_command_ssh(self, node: RemoteNode, command: str) -> Dict[str, Any]:
        """Execute command on remote node via SSH"""
        try:
            async with asyncssh.connect(
                node.hostname, 
                port=node.port,
                username=node.username,
                client_keys=[node.ssh_key_path] if node.ssh_key_path else None
            ) as conn:
                result = await conn.run(command)
                return {
                    'success': result.exit_status == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'exit_code': result.exit_status
                }
        except Exception as e:
            logger.error(f"SSH command failed on {node.node_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }
    
    async def execute_command_http(self, node: RemoteNode, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command on remote node via HTTP API"""
        try:
            url = f"http://{node.hostname}:{node.port}{endpoint}"
            headers = {}
            if node.api_token:
                headers['Authorization'] = f"Bearer {node.api_token}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    result = await response.json()
                    return {
                        'success': response.status == 200,
                        'data': result,
                        'status_code': response.status
                    }
        except Exception as e:
            logger.error(f"HTTP command failed on {node.node_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': -1
            }
    
    async def create_tunnel_on_node(self, node_id: str, tunnel: VxLANTunnel) -> Dict[str, Any]:
        """Create tunnel on specific remote node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        if node.connection_type == 'ssh':
            # Generate VxLAN creation commands
            commands = [
                f"ip link add {tunnel.interface_name} type vxlan id {tunnel.vni} "
                f"local {tunnel.local_ip} remote {tunnel.remote_ip} "
                f"dev {tunnel.physical_interface} dstport {tunnel.port}",
                f"ip link set {tunnel.interface_name} up",
                f"ip link add {tunnel.bridge_name} type bridge || true",
                f"ip link set {tunnel.bridge_name} up",
                f"ip link set {tunnel.interface_name} master {tunnel.bridge_name}",
                f"ip link set {tunnel.interface_name} mtu {tunnel.mtu}"
            ]
            
            results = []
            for cmd in commands:
                result = await self.execute_command_ssh(node, cmd)
                results.append(result)
                if not result['success']:
                    logger.error(f"Command failed on {node_id}: {cmd}")
                    break
            
            return {'node_id': node_id, 'results': results}
            
        elif node.connection_type == 'http':
            # Use HTTP API to create tunnel
            tunnel_data = {
                'vni': tunnel.vni,
                'local_ip': tunnel.local_ip,
                'remote_ip': tunnel.remote_ip,
                'interface_name': tunnel.interface_name,
                'bridge_name': tunnel.bridge_name,
                'physical_interface': tunnel.physical_interface,
                'mtu': tunnel.mtu,
                'port': tunnel.port
            }
            
            result = await self.execute_command_http(node, '/api/v1/tunnels', tunnel_data)
            return {'node_id': node_id, 'result': result}
    
    async def delete_tunnel_on_node(self, node_id: str, interface_name: str) -> Dict[str, Any]:
        """Delete tunnel on specific remote node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        if node.connection_type == 'ssh':
            commands = [
                f"ip link set {interface_name} nomaster",
                f"ip link delete {interface_name}"
            ]
            
            results = []
            for cmd in commands:
                result = await self.execute_command_ssh(node, cmd)
                results.append(result)
            
            return {'node_id': node_id, 'results': results}
            
        elif node.connection_type == 'http':
            tunnel_id = interface_name.replace('vxlan', '')
            result = await self.execute_command_http(node, f'/api/v1/tunnels/{tunnel_id}', {})
            return {'node_id': node_id, 'result': result}
    
    async def get_node_status(self, node_id: str) -> Dict[str, Any]:
        """Get status of remote node"""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        if node.connection_type == 'ssh':
            result = await self.execute_command_ssh(node, "ip -j link show type vxlan")
            return {'node_id': node_id, 'result': result}
            
        elif node.connection_type == 'http':
            result = await self.execute_command_http(node, '/api/v1/status', {})
            return {'node_id': node_id, 'result': result}
    
    async def deploy_topology(self, topology_type: str, node_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Deploy topology across multiple nodes"""
        results = {}
        
        if topology_type == 'hub-spoke':
            # Identify hub node
            hub_node = None
            spoke_nodes = []
            
            for node_id, config in node_configs.items():
                if config.get('role') == 'hub':
                    hub_node = node_id
                else:
                    spoke_nodes.append(node_id)
            
            if not hub_node:
                raise ValueError("Hub node not specified for hub-spoke topology")
            
            # Create tunnels from hub to each spoke
            for spoke_node in spoke_nodes:
                hub_config = node_configs[hub_node]
                spoke_config = node_configs[spoke_node]
                
                # Create tunnel on hub
                hub_tunnel = VxLANTunnel(
                    vni=spoke_config['vni'],
                    local_ip=hub_config['ip'],
                    remote_ip=spoke_config['ip'],
                    interface_name=f"vxlan{spoke_config['vni']}",
                    bridge_name=hub_config.get('bridge', 'br-lan'),
                    physical_interface=hub_config.get('interface', 'eth0')
                )
                
                # Create tunnel on spoke
                spoke_tunnel = VxLANTunnel(
                    vni=spoke_config['vni'],
                    local_ip=spoke_config['ip'],
                    remote_ip=hub_config['ip'],
                    interface_name=f"vxlan{spoke_config['vni']}",
                    bridge_name=spoke_config.get('bridge', 'br-lan'),
                    physical_interface=spoke_config.get('interface', 'eth0')
                )
                
                # Execute tunnel creation
                hub_result = await self.create_tunnel_on_node(hub_node, hub_tunnel)
                spoke_result = await self.create_tunnel_on_node(spoke_node, spoke_tunnel)
                
                results[f"{hub_node}-{spoke_node}"] = {
                    'hub': hub_result,
                    'spoke': spoke_result
                }
        
        return results
    
    def add_node(self, node: RemoteNode):
        """Add remote node to orchestrator"""
        self.nodes[node.node_id] = node
        self.save_node_configuration()
    
    def save_node_configuration(self):
        """Save node configuration to file"""
        try:
            import yaml
            data = {
                'nodes': {
                    node_id: {
                        'node_id': node.node_id,
                        'hostname': node.hostname,
                        'connection_type': node.connection_type,
                        'port': node.port,
                        'username': node.username,
                        'ssh_key_path': node.ssh_key_path,
                        'api_token': node.api_token
                    }
                    for node_id, node in self.nodes.items()
                }
            }
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save node configuration: {e}")
