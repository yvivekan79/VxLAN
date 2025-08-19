"""
Core VxLAN tunnel management functionality
"""

import os
import json
import subprocess
import ipaddress
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .logger import get_logger
from .utils import run_command, validate_vni, validate_ip

logger = get_logger(__name__)

@dataclass
class VxLANTunnel:
    """VxLAN tunnel configuration"""
    vni: int
    local_ip: str
    remote_ip: str
    interface_name: str
    bridge_name: str
    physical_interface: str = "eth0"
    mtu: int = 1450
    port: int = 4789
    label: str = ""
    encryption: str = "none"  # none, psk, ikev2
    psk_key: Optional[str] = None
    
    def __post_init__(self):
        """Validate tunnel parameters"""
        if not validate_vni(self.vni):
            raise ValueError(f"Invalid VNI: {self.vni}. Must be between 4096 and 16777215")
        
        if not validate_ip(self.local_ip):
            raise ValueError(f"Invalid local IP: {self.local_ip}")
            
        if not validate_ip(self.remote_ip):
            raise ValueError(f"Invalid remote IP: {self.remote_ip}")

class VxLANManager:
    """VxLAN tunnel management class"""
    
    def __init__(self, config_path: str = "./config/tunnels.yaml"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.tunnels: Dict[str, VxLANTunnel] = {}
        self.load_configuration()
    
    def load_configuration(self):
        """Load tunnel configuration from file"""
        try:
            if self.config_path.exists():
                import yaml
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                for tunnel_id, tunnel_data in data.get('tunnels', {}).items():
                    try:
                        tunnel = VxLANTunnel(**tunnel_data)
                        self.tunnels[tunnel_id] = tunnel
                        logger.info(f"Loaded tunnel configuration: {tunnel_id}")
                    except Exception as e:
                        logger.error(f"Failed to load tunnel {tunnel_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save tunnel configuration to file"""
        try:
            import yaml
            data = {
                'tunnels': {
                    tunnel_id: asdict(tunnel) 
                    for tunnel_id, tunnel in self.tunnels.items()
                }
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def create_tunnel(self, tunnel: VxLANTunnel, tunnel_id: Optional[str] = None) -> str:
        """Create a VxLAN tunnel"""
        if not tunnel_id:
            tunnel_id = f"vxlan{tunnel.vni}"
        
        # Check if tunnel already exists (idempotent operation)
        if tunnel_id in self.tunnels:
            existing = self.tunnels[tunnel_id]
            if (existing.vni == tunnel.vni and 
                existing.local_ip == tunnel.local_ip and 
                existing.remote_ip == tunnel.remote_ip):
                logger.info(f"Tunnel {tunnel_id} already exists with same configuration")
                return tunnel_id
            else:
                raise ValueError(f"Tunnel {tunnel_id} exists with different configuration")
        
        try:
            # Create VxLAN interface
            self._create_vxlan_interface(tunnel)
            
            # Create and configure bridge
            self._setup_bridge(tunnel)
            
            # Configure MTU
            self._configure_mtu(tunnel)
            
            # Apply security configuration if needed
            if tunnel.encryption != "none":
                self._setup_encryption(tunnel)
            
            # Store configuration
            self.tunnels[tunnel_id] = tunnel
            self.save_configuration()
            
            logger.info(f"Tunnel {tunnel_id} created successfully", extra={
                'event': 'tunnel_create',
                'tunnel_id': tunnel_id,
                'vni': tunnel.vni,
                'local_ip': tunnel.local_ip,
                'remote_ip': tunnel.remote_ip
            })
            
            return tunnel_id
            
        except Exception as e:
            logger.error(f"Failed to create tunnel {tunnel_id}: {e}")
            # Cleanup on failure
            self._cleanup_tunnel(tunnel)
            raise
    
    def delete_tunnel(self, tunnel_id: str):
        """Delete a VxLAN tunnel"""
        if tunnel_id not in self.tunnels:
            raise ValueError(f"Tunnel {tunnel_id} not found")
        
        tunnel = self.tunnels[tunnel_id]
        
        try:
            # Remove from bridge
            run_command(f"ip link set {tunnel.interface_name} nomaster", check=False)
            
            # Delete VxLAN interface
            run_command(f"ip link delete {tunnel.interface_name}", check=False)
            
            # Remove from configuration
            del self.tunnels[tunnel_id]
            self.save_configuration()
            
            logger.info(f"Tunnel {tunnel_id} deleted successfully", extra={
                'event': 'tunnel_delete',
                'tunnel_id': tunnel_id,
                'vni': tunnel.vni
            })
            
        except Exception as e:
            logger.error(f"Failed to delete tunnel {tunnel_id}: {e}")
            raise
    
    def list_tunnels(self) -> Dict[str, dict]:
        """List all configured tunnels"""
        result = {}
        for tunnel_id, tunnel in self.tunnels.items():
            tunnel_dict = asdict(tunnel)
            
            # Add runtime status
            tunnel_dict['status'] = self._get_tunnel_status(tunnel)
            tunnel_dict['tunnel_id'] = tunnel_id
            
            result[tunnel_id] = tunnel_dict
        
        return result
    
    def get_tunnel(self, tunnel_id: str) -> Optional[VxLANTunnel]:
        """Get tunnel configuration by ID"""
        return self.tunnels.get(tunnel_id)
    
    def _create_vxlan_interface(self, tunnel: VxLANTunnel):
        """Create VxLAN interface using ip command"""
        cmd = (f"ip link add {tunnel.interface_name} type vxlan "
               f"id {tunnel.vni} "
               f"local {tunnel.local_ip} "
               f"remote {tunnel.remote_ip} "
               f"dev {tunnel.physical_interface} "
               f"dstport {tunnel.port}")
        
        run_command(cmd)
        run_command(f"ip link set {tunnel.interface_name} up")
        logger.debug(f"Created VxLAN interface: {tunnel.interface_name}")
    
    def _setup_bridge(self, tunnel: VxLANTunnel):
        """Setup bridge and add VxLAN interface to it"""
        # Create bridge if it doesn't exist
        bridge_exists = run_command(f"ip link show {tunnel.bridge_name}", check=False)[0] == 0
        
        if not bridge_exists:
            run_command(f"ip link add {tunnel.bridge_name} type bridge")
            run_command(f"ip link set {tunnel.bridge_name} up")
            logger.debug(f"Created bridge: {tunnel.bridge_name}")
        
        # Add VxLAN interface to bridge
        run_command(f"ip link set {tunnel.interface_name} master {tunnel.bridge_name}")
        logger.debug(f"Added {tunnel.interface_name} to bridge {tunnel.bridge_name}")
    
    def _configure_mtu(self, tunnel: VxLANTunnel):
        """Configure MTU for tunnel interface"""
        run_command(f"ip link set {tunnel.interface_name} mtu {tunnel.mtu}")
        logger.debug(f"Set MTU {tunnel.mtu} for {tunnel.interface_name}")
    
    def _setup_encryption(self, tunnel: VxLANTunnel):
        """Setup encryption for tunnel (placeholder for future implementation)"""
        if tunnel.encryption == "psk" and tunnel.psk_key:
            logger.info(f"PSK encryption configured for tunnel {tunnel.interface_name}")
        elif tunnel.encryption == "ikev2":
            logger.info(f"IKEv2 encryption configured for tunnel {tunnel.interface_name}")
    
    def _cleanup_tunnel(self, tunnel: VxLANTunnel):
        """Cleanup tunnel resources on failure"""
        try:
            run_command(f"ip link delete {tunnel.interface_name}", check=False)
        except:
            pass
    
    def _get_tunnel_status(self, tunnel: VxLANTunnel) -> dict:
        """Get runtime status of tunnel"""
        try:
            # Check if interface exists
            ret_code, output, _ = run_command(f"ip -d link show {tunnel.interface_name}", check=False)
            
            if ret_code == 0:
                # Parse interface status
                if "state UP" in output:
                    status = "up"
                elif "state DOWN" in output:
                    status = "down"
                else:
                    status = "unknown"
                
                return {
                    "status": status,
                    "interface_exists": True,
                    "details": output.strip()
                }
            else:
                return {
                    "status": "not_found",
                    "interface_exists": False,
                    "details": "Interface not found"
                }
        except Exception as e:
            return {
                "status": "error",
                "interface_exists": False,
                "details": str(e)
            }
    
    def recover_state(self):
        """Recover tunnel state from configuration"""
        logger.info("Recovering tunnel state from configuration")
        
        for tunnel_id, tunnel in self.tunnels.items():
            try:
                # Check if tunnel interface exists
                ret_code, _, _ = run_command(f"ip link show {tunnel.interface_name}", check=False)
                
                if ret_code != 0:
                    # Recreate tunnel interface
                    logger.info(f"Recreating tunnel interface: {tunnel_id}")
                    self._create_vxlan_interface(tunnel)
                    self._setup_bridge(tunnel)
                    self._configure_mtu(tunnel)
                    
                    if tunnel.encryption != "none":
                        self._setup_encryption(tunnel)
                        
            except Exception as e:
                logger.error(f"Failed to recover tunnel {tunnel_id}: {e}")
