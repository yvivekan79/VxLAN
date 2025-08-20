"""
Configuration management for VxLAN tunnel system
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .logger import get_logger

logger = get_logger(__name__)

DEFAULT_APP_CONFIG = {
    'api_port': 8000,
    'log_level': 'INFO',
    'log_file': './logs/gind-tunnels.log',
    'config_dir': './config',
    'tunnel_config_file': './config/tunnels.yaml',
    'backup_configs': True,
    'auto_recover': True,
    'default_mtu': 1450,
    'default_bridge': 'br-lan',
    'default_physical_interface': 'eth0'
}

def load_app_config(config_path: str = './config/app_config.yaml') -> Dict[str, Any]:
    """Load application configuration"""
    config_file = Path(config_path)
    
    try:
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Merge with defaults
            merged_config = DEFAULT_APP_CONFIG.copy()
            merged_config.update(config)
            
            logger.info(f"Loaded configuration from {config_path}")
            return merged_config
        else:
            logger.info("No configuration file found, using defaults")
            return DEFAULT_APP_CONFIG.copy()
            
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info("Using default configuration")
        return DEFAULT_APP_CONFIG.copy()

def save_app_config(config: Dict[str, Any], config_path: str = './config/app_config.yaml'):
    """Save application configuration"""
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise

def ensure_config_directory(config_dir: str = './config'):
    """Ensure configuration directory exists"""
    config_path = Path(config_dir)
    config_path.mkdir(parents=True, exist_ok=True)
    
    # Set appropriate permissions
    try:
        os.chmod(config_path, 0o755)
    except:
        pass

class ConfigManager:
    """Configuration manager class"""
    
    def __init__(self, config_dir: str = './config'):
        self.config_dir = Path(config_dir)
        self.app_config_file = self.config_dir / 'app_config.yaml'
        self.tunnel_config_file = self.config_dir / 'tunnels.yaml'
        
        # Ensure directory exists
        ensure_config_directory(str(self.config_dir))
        
        # Load configuration
        self.app_config = self.load_app_config()
    
    def load_app_config(self) -> Dict[str, Any]:
        """Load application configuration"""
        return load_app_config(str(self.app_config_file))
    
    def save_app_config(self, config: Dict[str, Any]):
        """Save application configuration"""
        save_app_config(config, str(self.app_config_file))
        self.app_config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.app_config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.app_config[key] = value
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_keys = ['api_port', 'log_level', 'log_file', 'config_dir']
        
        for key in required_keys:
            if key not in self.app_config:
                logger.error(f"Missing required configuration key: {key}")
                return False
        
        # Validate port
        port = self.app_config.get('api_port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            logger.error(f"Invalid API port: {port}")
            return False
        
        # Validate log level
        log_level = self.app_config.get('log_level', '').upper()
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            logger.error(f"Invalid log level: {log_level}")
            return False
        
        return True
    
    def backup_config(self, config_type: str = 'tunnels'):
        """Create backup of configuration"""
        if not self.app_config.get('backup_configs', True):
            return
        
        try:
            import shutil
            from datetime import datetime
            
            if config_type == 'tunnels':
                source = self.tunnel_config_file
            else:
                source = self.app_config_file
            
            if source.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{source.name}.backup_{timestamp}"
                backup_path = source.parent / backup_name
                
                shutil.copy2(source, backup_path)
                logger.info(f"Configuration backed up to {backup_path}")
                
                # Keep only last 10 backups
                self._cleanup_old_backups(source.parent, source.name)
                
        except Exception as e:
            logger.error(f"Failed to backup configuration: {e}")
    
    def _cleanup_old_backups(self, backup_dir: Path, base_name: str, keep_count: int = 10):
        """Cleanup old backup files"""
        try:
            backup_files = list(backup_dir.glob(f"{base_name}.backup_*"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
