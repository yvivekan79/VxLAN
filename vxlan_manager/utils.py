"""
Utility functions for VxLAN tunnel management
"""

import subprocess
import ipaddress
import re
from typing import Tuple, Optional, List
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)

def run_command(command: str, check: bool = True, timeout: int = 30) -> Tuple[int, str, str]:
    """
    Run a system command and return result
    
    Args:
        command: Command to run
        check: Whether to raise exception on non-zero exit code
        timeout: Command timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        logger.debug(f"Running command: {command}")
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        logger.debug(f"Command result: rc={result.returncode}, "
                    f"stdout={result.stdout[:200]}{'...' if len(result.stdout) > 200 else ''}")
        
        if check and result.returncode != 0:
            logger.error(f"Command failed: {command}")
            logger.error(f"Return code: {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {command}")
        raise
    except Exception as e:
        logger.error(f"Command execution failed: {command}, error: {e}")
        if check:
            raise
        return -1, "", str(e)

def validate_ip(ip_address: str) -> bool:
    """
    Validate IP address format
    
    Args:
        ip_address: IP address string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False

def validate_vni(vni: int) -> bool:
    """
    Validate VxLAN Network Identifier
    
    Args:
        vni: VNI value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(vni, int) and 4096 <= vni <= 16777215

def validate_port(port: int) -> bool:
    """
    Validate port number
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(port, int) and 1 <= port <= 65535

def validate_mtu(mtu: int) -> bool:
    """
    Validate MTU value
    
    Args:
        mtu: MTU value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(mtu, int) and 1280 <= mtu <= 9000

def calculate_mtu(underlay_mtu: int = 1500, encapsulation_overhead: int = 50) -> int:
    """
    Calculate optimal MTU for VxLAN tunnel
    
    Args:
        underlay_mtu: MTU of underlay network
        encapsulation_overhead: VxLAN encapsulation overhead
        
    Returns:
        Calculated MTU value
    """
    return underlay_mtu - encapsulation_overhead

def check_interface_exists(interface_name: str) -> bool:
    """
    Check if network interface exists
    
    Args:
        interface_name: Name of interface to check
        
    Returns:
        True if interface exists, False otherwise
    """
    try:
        ret_code, _, _ = run_command(f"ip link show {interface_name}", check=False)
        return ret_code == 0
    except:
        return False

def check_bridge_exists(bridge_name: str) -> bool:
    """
    Check if bridge exists
    
    Args:
        bridge_name: Name of bridge to check
        
    Returns:
        True if bridge exists, False otherwise
    """
    try:
        ret_code, _, _ = run_command(f"ip link show {bridge_name} type bridge", check=False)
        return ret_code == 0
    except:
        return False

def get_interface_info(interface_name: str) -> Optional[dict]:
    """
    Get detailed information about network interface
    
    Args:
        interface_name: Name of interface
        
    Returns:
        Dictionary with interface information or None if not found
    """
    try:
        ret_code, output, _ = run_command(f"ip -j link show {interface_name}", check=False)
        if ret_code == 0 and output.strip():
            import json
            interface_data = json.loads(output)
            return interface_data[0] if interface_data else None
    except:
        pass
    
    return None

def get_bridge_info(bridge_name: str) -> Optional[dict]:
    """
    Get detailed information about bridge
    
    Args:
        bridge_name: Name of bridge
        
    Returns:
        Dictionary with bridge information or None if not found
    """
    try:
        ret_code, output, _ = run_command(f"bridge -j link show", check=False)
        if ret_code == 0 and output.strip():
            import json
            bridge_data = json.loads(output)
            bridge_info = {
                'name': bridge_name,
                'interfaces': []
            }
            
            for entry in bridge_data:
                if entry.get('master') == bridge_name:
                    bridge_info['interfaces'].append(entry.get('ifname'))
            
            return bridge_info if bridge_info['interfaces'] else None
    except:
        pass
    
    return None

def check_kernel_modules(required_modules: List[str] = None) -> dict:
    """
    Check if required kernel modules are loaded
    
    Args:
        required_modules: List of required modules (default: vxlan, br_netfilter)
        
    Returns:
        Dictionary with module status
    """
    if required_modules is None:
        required_modules = ['vxlan', 'br_netfilter']
    
    module_status = {}
    
    try:
        ret_code, output, _ = run_command("lsmod", check=False)
        if ret_code == 0:
            loaded_modules = output.lower()
            
            for module in required_modules:
                module_status[module] = module.lower() in loaded_modules
        else:
            # Fallback: check individual modules
            for module in required_modules:
                ret_code, _, _ = run_command(f"lsmod | grep -q {module}", check=False)
                module_status[module] = ret_code == 0
                
    except Exception as e:
        logger.error(f"Failed to check kernel modules: {e}")
        for module in required_modules:
            module_status[module] = False
    
    return module_status

def load_kernel_module(module_name: str) -> bool:
    """
    Load kernel module
    
    Args:
        module_name: Name of module to load
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ret_code, _, _ = run_command(f"modprobe {module_name}", check=False)
        return ret_code == 0
    except:
        return False

def ensure_kernel_modules(required_modules: List[str] = None) -> bool:
    """
    Ensure required kernel modules are loaded
    
    Args:
        required_modules: List of required modules
        
    Returns:
        True if all modules are loaded, False otherwise
    """
    if required_modules is None:
        required_modules = ['vxlan', 'br_netfilter']
    
    module_status = check_kernel_modules(required_modules)
    all_loaded = True
    
    for module, loaded in module_status.items():
        if not loaded:
            logger.info(f"Loading kernel module: {module}")
            if load_kernel_module(module):
                logger.info(f"Successfully loaded module: {module}")
            else:
                logger.error(f"Failed to load module: {module}")
                all_loaded = False
    
    return all_loaded

def check_system_requirements() -> dict:
    """
    Check system requirements for VxLAN tunnels
    
    Returns:
        Dictionary with system requirement status
    """
    requirements = {
        'kernel_version': None,
        'kernel_modules': {},
        'ip_command': False,
        'bridge_command': False,
        'permissions': False
    }
    
    # Check kernel version
    try:
        ret_code, output, _ = run_command("uname -r", check=False)
        if ret_code == 0:
            requirements['kernel_version'] = output.strip()
    except:
        pass
    
    # Check kernel modules
    requirements['kernel_modules'] = check_kernel_modules()
    
    # Check required commands
    for command in ['ip', 'bridge']:
        try:
            ret_code, _, _ = run_command(f"which {command}", check=False)
            requirements[f'{command}_command'] = ret_code == 0
        except:
            requirements[f'{command}_command'] = False
    
    # Check permissions (can we run ip commands?)
    try:
        ret_code, _, _ = run_command("ip link show", check=False)
        requirements['permissions'] = ret_code == 0
    except:
        requirements['permissions'] = False
    
    return requirements

def parse_interface_name(name: str) -> Optional[dict]:
    """
    Parse VxLAN interface name to extract information
    
    Args:
        name: Interface name (e.g., vxlan100, vxlan-site1-100)
        
    Returns:
        Dictionary with parsed information or None
    """
    # Pattern for vxlan interfaces
    patterns = [
        r'^vxlan(\d+)$',  # vxlan100
        r'^vxlan-([^-]+)-(\d+)$',  # vxlan-site1-100
        r'^vxlan-([^-]+)-([^-]+)-(\d+)$'  # vxlan-site1-site2-100
    ]
    
    for pattern in patterns:
        match = re.match(pattern, name)
        if match:
            groups = match.groups()
            
            if len(groups) == 1:  # vxlan100
                return {
                    'type': 'simple',
                    'vni': int(groups[0]),
                    'labels': []
                }
            elif len(groups) == 2:  # vxlan-site1-100
                return {
                    'type': 'labeled',
                    'vni': int(groups[1]),
                    'labels': [groups[0]]
                }
            elif len(groups) == 3:  # vxlan-site1-site2-100
                return {
                    'type': 'connection',
                    'vni': int(groups[2]),
                    'labels': [groups[0], groups[1]]
                }
    
    return None

def generate_interface_name(vni: int, labels: List[str] = None) -> str:
    """
    Generate VxLAN interface name
    
    Args:
        vni: VxLAN Network Identifier
        labels: Optional labels for interface naming
        
    Returns:
        Generated interface name
    """
    if not labels:
        return f"vxlan{vni}"
    elif len(labels) == 1:
        return f"vxlan-{labels[0]}-{vni}"
    elif len(labels) == 2:
        return f"vxlan-{labels[0]}-{labels[1]}-{vni}"
    else:
        # Truncate and join multiple labels
        label_str = "-".join(labels[:2])
        return f"vxlan-{label_str}-{vni}"
