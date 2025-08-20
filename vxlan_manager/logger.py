"""
Logging configuration for VxLAN tunnel management system
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# IPFIX-compliant log format
class IPFIXFormatter(logging.Formatter):
    """Custom formatter for IPFIX-compliant logging"""
    
    def format(self, record):
        # Create IPFIX-like structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'source_file': record.pathname,
            'source_line': record.lineno,
            'function': record.funcName
        }
        
        # Add extra fields from record
        extra_fields = getattr(record, 'extra', {})
        if hasattr(record, 'event'):
            log_entry['event'] = record.event
        if hasattr(record, 'tunnel_id'):
            log_entry['tunnel_id'] = record.tunnel_id
        if hasattr(record, 'vni'):
            log_entry['vni'] = record.vni
        if hasattr(record, 'local_ip'):
            log_entry['local_ip'] = record.local_ip
        if hasattr(record, 'remote_ip'):
            log_entry['remote_ip'] = record.remote_ip
        
        # Add any additional extra fields
        for key, value in extra_fields.items():
            if key not in log_entry:
                log_entry[key] = value
        
        return json.dumps(log_entry, separators=(',', ':'))

def setup_logging(log_file: str = './logs/gind-tunnels.log', 
                  log_level: str = 'INFO',
                  enable_console: bool = True):
    """Setup logging configuration"""
    
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # File handler with IPFIX formatter
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(IPFIXFormatter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging to {log_file}: {e}")
    
    # Console handler with simple formatter (if enabled)
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Set logging levels for third-party libraries
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

class TunnelLogger:
    """Specialized logger for tunnel events"""
    
    def __init__(self, logger_name: str = 'vxlan_manager.tunnel'):
        self.logger = get_logger(logger_name)
    
    def tunnel_created(self, tunnel_id: str, vni: int, local_ip: str, remote_ip: str, **kwargs):
        """Log tunnel creation event"""
        self.logger.info(
            f"Tunnel {tunnel_id} created successfully",
            extra={
                'event': 'tunnel_create',
                'tunnel_id': tunnel_id,
                'vni': vni,
                'local_ip': local_ip,
                'remote_ip': remote_ip,
                **kwargs
            }
        )
    
    def tunnel_deleted(self, tunnel_id: str, vni: int, **kwargs):
        """Log tunnel deletion event"""
        self.logger.info(
            f"Tunnel {tunnel_id} deleted successfully",
            extra={
                'event': 'tunnel_delete',
                'tunnel_id': tunnel_id,
                'vni': vni,
                **kwargs
            }
        )
    
    def tunnel_modified(self, tunnel_id: str, changes: Dict[str, Any], **kwargs):
        """Log tunnel modification event"""
        self.logger.info(
            f"Tunnel {tunnel_id} modified",
            extra={
                'event': 'tunnel_modify',
                'tunnel_id': tunnel_id,
                'changes': changes,
                **kwargs
            }
        )
    
    def tunnel_status_change(self, tunnel_id: str, old_status: str, new_status: str, **kwargs):
        """Log tunnel status change"""
        self.logger.info(
            f"Tunnel {tunnel_id} status changed from {old_status} to {new_status}",
            extra={
                'event': 'tunnel_status_change',
                'tunnel_id': tunnel_id,
                'old_status': old_status,
                'new_status': new_status,
                **kwargs
            }
        )
    
    def tunnel_error(self, tunnel_id: str, error_message: str, **kwargs):
        """Log tunnel error"""
        self.logger.error(
            f"Tunnel {tunnel_id} error: {error_message}",
            extra={
                'event': 'tunnel_error',
                'tunnel_id': tunnel_id,
                'error_message': error_message,
                **kwargs
            }
        )
    
    def topology_created(self, topology_type: str, tunnel_count: int, **kwargs):
        """Log topology creation event"""
        self.logger.info(
            f"Topology {topology_type} created with {tunnel_count} tunnels",
            extra={
                'event': 'topology_create',
                'topology_type': topology_type,
                'tunnel_count': tunnel_count,
                **kwargs
            }
        )
    
    def state_recovery(self, recovered_tunnels: int, failed_tunnels: int = 0, **kwargs):
        """Log state recovery event"""
        self.logger.info(
            f"State recovery completed: {recovered_tunnels} tunnels recovered, {failed_tunnels} failed",
            extra={
                'event': 'state_recovery',
                'recovered_tunnels': recovered_tunnels,
                'failed_tunnels': failed_tunnels,
                **kwargs
            }
        )

# Global tunnel logger instance
tunnel_logger = TunnelLogger()
