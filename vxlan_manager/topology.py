"""
Network topology management for VxLAN tunnels
"""

from typing import Dict, List, Optional, Any, Tuple
from itertools import combinations
import ipaddress

from .core import VxLANManager, VxLANTunnel
from .logger import get_logger, tunnel_logger

logger = get_logger(__name__)

class TopologyManager:
    """Manager for network topology creation and management"""
    
    def __init__(self, vxlan_manager: VxLANManager):
        self.vxlan_manager = vxlan_manager
    
    def create_topology(self, topology_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create network topology"""
        if topology_type == 'hub-spoke':
            return self._create_hub_spoke(config)
        elif topology_type == 'full-mesh':
            return self._create_full_mesh(config)
        elif topology_type == 'partial-mesh':
            return self._create_partial_mesh(config)
        else:
            raise ValueError(f"Unsupported topology type: {topology_type}")
    
    def plan_topology(self, topology_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Plan topology without creating tunnels (dry run)"""
        if topology_type == 'hub-spoke':
            return self._plan_hub_spoke(config)
        elif topology_type == 'full-mesh':
            return self._plan_full_mesh(config)
        elif topology_type == 'partial-mesh':
            return self._plan_partial_mesh(config)
        else:
            raise ValueError(f"Unsupported topology type: {topology_type}")
    
    def _create_hub_spoke(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create hub-spoke topology"""
        nodes = config.get('nodes', {})
        hub_config = config.get('hub', {})
        
        if not hub_config:
            raise ValueError("Hub configuration is required for hub-spoke topology")
        
        hub_node = hub_config.get('node')
        if hub_node not in nodes:
            raise ValueError(f"Hub node '{hub_node}' not found in nodes configuration")
        
        hub_info = nodes[hub_node]
        base_vni = config.get('base_vni', 100)
        bridge_name = config.get('bridge_name', 'br-lan')
        
        created_tunnels = {}
        vni_counter = base_vni
        
        # Create tunnels from hub to each spoke
        for spoke_node, spoke_info in nodes.items():
            if spoke_node == hub_node:
                continue
                
            try:
                # Hub to spoke tunnel
                hub_tunnel_id = f"hub-{spoke_node}-{vni_counter}"
                hub_tunnel = VxLANTunnel(
                    vni=vni_counter,
                    local_ip=hub_info['wan_ip'],
                    remote_ip=spoke_info['wan_ip'],
                    interface_name=f"vxlan{vni_counter}",
                    bridge_name=bridge_name,
                    physical_interface=hub_info.get('physical_interface', 'eth0'),
                    mtu=config.get('mtu', 1450),
                    label=f"hub-spoke-{spoke_node}"
                )
                
                tunnel_id = self.vxlan_manager.create_tunnel(hub_tunnel, hub_tunnel_id)
                created_tunnels[tunnel_id] = {
                    'tunnel_id': tunnel_id,
                    'type': 'hub-spoke',
                    'hub_node': hub_node,
                    'spoke_node': spoke_node,
                    'vni': vni_counter,
                    'local_ip': hub_info['wan_ip'],
                    'remote_ip': spoke_info['wan_ip']
                }
                
                vni_counter += 1
                
            except Exception as e:
                logger.error(f"Failed to create hub-spoke tunnel for {spoke_node}: {e}")
                raise
        
        tunnel_logger.topology_created('hub-spoke', len(created_tunnels))
        return created_tunnels
    
    def _create_full_mesh(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create full mesh topology"""
        nodes = config.get('nodes', {})
        base_vni = config.get('base_vni', 100)
        bridge_name = config.get('bridge_name', 'br-lan')
        
        created_tunnels = {}
        vni_counter = base_vni
        
        # Create tunnels between all pairs of nodes
        node_pairs = list(combinations(nodes.keys(), 2))
        
        for node1, node2 in node_pairs:
            node1_info = nodes[node1]
            node2_info = nodes[node2]
            
            try:
                # Create tunnel from node1 to node2
                tunnel_id = f"mesh-{node1}-{node2}-{vni_counter}"
                tunnel = VxLANTunnel(
                    vni=vni_counter,
                    local_ip=node1_info['wan_ip'],
                    remote_ip=node2_info['wan_ip'],
                    interface_name=f"vxlan{vni_counter}",
                    bridge_name=bridge_name,
                    physical_interface=node1_info.get('physical_interface', 'eth0'),
                    mtu=config.get('mtu', 1450),
                    label=f"mesh-{node1}-{node2}"
                )
                
                created_tunnel_id = self.vxlan_manager.create_tunnel(tunnel, tunnel_id)
                created_tunnels[created_tunnel_id] = {
                    'tunnel_id': created_tunnel_id,
                    'type': 'full-mesh',
                    'node1': node1,
                    'node2': node2,
                    'vni': vni_counter,
                    'local_ip': node1_info['wan_ip'],
                    'remote_ip': node2_info['wan_ip']
                }
                
                vni_counter += 1
                
            except Exception as e:
                logger.error(f"Failed to create mesh tunnel between {node1} and {node2}: {e}")
                raise
        
        tunnel_logger.topology_created('full-mesh', len(created_tunnels))
        return created_tunnels
    
    def _create_partial_mesh(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create partial mesh topology"""
        nodes = config.get('nodes', {})
        connections = config.get('connections', [])
        base_vni = config.get('base_vni', 100)
        bridge_name = config.get('bridge_name', 'br-lan')
        
        if not connections:
            raise ValueError("Connections list is required for partial mesh topology")
        
        created_tunnels = {}
        vni_counter = base_vni
        
        # Create tunnels for specified connections
        for connection in connections:
            node1 = connection.get('node1')
            node2 = connection.get('node2')
            
            if node1 not in nodes:
                raise ValueError(f"Node '{node1}' not found in nodes configuration")
            if node2 not in nodes:
                raise ValueError(f"Node '{node2}' not found in nodes configuration")
            
            node1_info = nodes[node1]
            node2_info = nodes[node2]
            
            try:
                # Create tunnel from node1 to node2
                tunnel_id = f"partial-{node1}-{node2}-{vni_counter}"
                tunnel = VxLANTunnel(
                    vni=vni_counter,
                    local_ip=node1_info['wan_ip'],
                    remote_ip=node2_info['wan_ip'],
                    interface_name=f"vxlan{vni_counter}",
                    bridge_name=bridge_name,
                    physical_interface=node1_info.get('physical_interface', 'eth0'),
                    mtu=config.get('mtu', 1450),
                    label=f"partial-{node1}-{node2}"
                )
                
                created_tunnel_id = self.vxlan_manager.create_tunnel(tunnel, tunnel_id)
                created_tunnels[created_tunnel_id] = {
                    'tunnel_id': created_tunnel_id,
                    'type': 'partial-mesh',
                    'node1': node1,
                    'node2': node2,
                    'vni': vni_counter,
                    'local_ip': node1_info['wan_ip'],
                    'remote_ip': node2_info['wan_ip']
                }
                
                vni_counter += 1
                
            except Exception as e:
                logger.error(f"Failed to create partial mesh tunnel between {node1} and {node2}: {e}")
                raise
        
        tunnel_logger.topology_created('partial-mesh', len(created_tunnels))
        return created_tunnels
    
    def _plan_hub_spoke(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Plan hub-spoke topology (dry run)"""
        nodes = config.get('nodes', {})
        hub_config = config.get('hub', {})
        
        if not hub_config:
            raise ValueError("Hub configuration is required for hub-spoke topology")
        
        hub_node = hub_config.get('node')
        if hub_node not in nodes:
            raise ValueError(f"Hub node '{hub_node}' not found in nodes configuration")
        
        hub_info = nodes[hub_node]
        base_vni = config.get('base_vni', 100)
        
        planned_tunnels = {}
        vni_counter = base_vni
        
        # Plan tunnels from hub to each spoke
        for spoke_node, spoke_info in nodes.items():
            if spoke_node == hub_node:
                continue
                
            tunnel_id = f"hub-{spoke_node}-{vni_counter}"
            planned_tunnels[tunnel_id] = {
                'tunnel_id': tunnel_id,
                'type': 'hub-spoke',
                'hub_node': hub_node,
                'spoke_node': spoke_node,
                'vni': vni_counter,
                'local_ip': hub_info['wan_ip'],
                'remote_ip': spoke_info['wan_ip'],
                'interface_name': f"vxlan{vni_counter}",
                'bridge_name': config.get('bridge_name', 'br-lan')
            }
            vni_counter += 1
        
        return planned_tunnels
    
    def _plan_full_mesh(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Plan full mesh topology (dry run)"""
        nodes = config.get('nodes', {})
        base_vni = config.get('base_vni', 100)
        
        planned_tunnels = {}
        vni_counter = base_vni
        
        # Plan tunnels between all pairs of nodes
        node_pairs = list(combinations(nodes.keys(), 2))
        
        for node1, node2 in node_pairs:
            node1_info = nodes[node1]
            node2_info = nodes[node2]
            
            tunnel_id = f"mesh-{node1}-{node2}-{vni_counter}"
            planned_tunnels[tunnel_id] = {
                'tunnel_id': tunnel_id,
                'type': 'full-mesh',
                'node1': node1,
                'node2': node2,
                'vni': vni_counter,
                'local_ip': node1_info['wan_ip'],
                'remote_ip': node2_info['wan_ip'],
                'interface_name': f"vxlan{vni_counter}",
                'bridge_name': config.get('bridge_name', 'br-lan')
            }
            vni_counter += 1
        
        return planned_tunnels
    
    def _plan_partial_mesh(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Plan partial mesh topology (dry run)"""
        nodes = config.get('nodes', {})
        connections = config.get('connections', [])
        base_vni = config.get('base_vni', 100)
        
        if not connections:
            raise ValueError("Connections list is required for partial mesh topology")
        
        planned_tunnels = {}
        vni_counter = base_vni
        
        # Plan tunnels for specified connections
        for connection in connections:
            node1 = connection.get('node1')
            node2 = connection.get('node2')
            
            if node1 not in nodes:
                raise ValueError(f"Node '{node1}' not found in nodes configuration")
            if node2 not in nodes:
                raise ValueError(f"Node '{node2}' not found in nodes configuration")
            
            node1_info = nodes[node1]
            node2_info = nodes[node2]
            
            tunnel_id = f"partial-{node1}-{node2}-{vni_counter}"
            planned_tunnels[tunnel_id] = {
                'tunnel_id': tunnel_id,
                'type': 'partial-mesh',
                'node1': node1,
                'node2': node2,
                'vni': vni_counter,
                'local_ip': node1_info['wan_ip'],
                'remote_ip': node2_info['wan_ip'],
                'interface_name': f"vxlan{vni_counter}",
                'bridge_name': config.get('bridge_name', 'br-lan')
            }
            vni_counter += 1
        
        return planned_tunnels
    
    def validate_topology_config(self, topology_type: str, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate topology configuration"""
        errors = []
        
        # Common validations
        nodes = config.get('nodes', {})
        if not nodes:
            errors.append("Nodes configuration is required")
            return False, errors
        
        # Validate node configurations
        for node_name, node_config in nodes.items():
            if not isinstance(node_config, dict):
                errors.append(f"Node '{node_name}' must be a dictionary")
                continue
                
            # Check required fields
            if 'wan_ip' not in node_config:
                errors.append(f"Node '{node_name}' missing 'wan_ip' field")
            else:
                # Validate IP address
                try:
                    ipaddress.ip_address(node_config['wan_ip'])
                except ValueError:
                    errors.append(f"Node '{node_name}' has invalid wan_ip: {node_config['wan_ip']}")
        
        # Topology-specific validations
        if topology_type == 'hub-spoke':
            hub_config = config.get('hub', {})
            if not hub_config:
                errors.append("Hub configuration is required for hub-spoke topology")
            else:
                hub_node = hub_config.get('node')
                if not hub_node:
                    errors.append("Hub node must be specified")
                elif hub_node not in nodes:
                    errors.append(f"Hub node '{hub_node}' not found in nodes configuration")
        
        elif topology_type == 'partial-mesh':
            connections = config.get('connections', [])
            if not connections:
                errors.append("Connections list is required for partial mesh topology")
            else:
                for i, connection in enumerate(connections):
                    if not isinstance(connection, dict):
                        errors.append(f"Connection {i} must be a dictionary")
                        continue
                    
                    node1 = connection.get('node1')
                    node2 = connection.get('node2')
                    
                    if not node1:
                        errors.append(f"Connection {i} missing 'node1' field")
                    elif node1 not in nodes:
                        errors.append(f"Connection {i} references unknown node '{node1}'")
                    
                    if not node2:
                        errors.append(f"Connection {i} missing 'node2' field")
                    elif node2 not in nodes:
                        errors.append(f"Connection {i} references unknown node '{node2}'")
                    
                    if node1 == node2:
                        errors.append(f"Connection {i} cannot connect node to itself")
        
        # Validate VNI ranges
        base_vni = config.get('base_vni', 100)
        if not isinstance(base_vni, int) or base_vni < 4096 or base_vni > 16777215:
            errors.append(f"Invalid base_vni: {base_vni}. Must be between 4096 and 16777215")
        
        return len(errors) == 0, errors
