
"""
Advanced API endpoints for VxLAN tunnel management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime

from .core import VxLANManager, VxLANTunnel
from .orchestrator import VxLANOrchestrator
from .logger import get_logger

logger = get_logger(__name__)

class BulkTunnelOperation(BaseModel):
    operation: str  # create, delete, update
    tunnels: List[Dict[str, Any]]

class NetworkMetrics(BaseModel):
    timestamp: datetime
    tunnel_id: str
    bytes_sent: int
    bytes_received: int
    packets_sent: int
    packets_received: int
    errors: int

def create_advanced_router(manager: VxLANManager, orchestrator: VxLANOrchestrator) -> APIRouter:
    """Create advanced API router"""
    
    router = APIRouter(prefix="/api/v1/advanced", tags=["advanced"])
    
    @router.post("/bulk-operations")
    async def bulk_operations(request: BulkTunnelOperation):
        """Perform bulk operations on multiple tunnels"""
        try:
            results = []
            
            for tunnel_data in request.tunnels:
                try:
                    if request.operation == "create":
                        tunnel = VxLANTunnel(**tunnel_data)
                        tunnel_id = manager.create_tunnel(tunnel)
                        results.append({"success": True, "tunnel_id": tunnel_id})
                    
                    elif request.operation == "delete":
                        tunnel_id = tunnel_data.get("tunnel_id")
                        manager.delete_tunnel(tunnel_id)
                        results.append({"success": True, "tunnel_id": tunnel_id})
                    
                    elif request.operation == "update":
                        tunnel_id = tunnel_data.pop("tunnel_id")
                        manager.delete_tunnel(tunnel_id)
                        tunnel = VxLANTunnel(**tunnel_data)
                        new_tunnel_id = manager.create_tunnel(tunnel, tunnel_id)
                        results.append({"success": True, "tunnel_id": new_tunnel_id})
                        
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            
            success_count = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "message": f"Bulk operation completed: {success_count}/{len(results)} successful",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Bulk operation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk operation failed: {e}"
            )
    
    @router.get("/network-metrics/{tunnel_id}")
    async def get_network_metrics(tunnel_id: str):
        """Get network metrics for a specific tunnel"""
        try:
            if tunnel_id not in manager.tunnels:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tunnel {tunnel_id} not found"
                )
            
            tunnel = manager.tunnels[tunnel_id]
            
            # Get interface statistics
            from .utils import run_command
            ret_code, output, _ = run_command(
                f"cat /sys/class/net/{tunnel.interface_name}/statistics/rx_bytes",
                check=False
            )
            rx_bytes = int(output.strip()) if ret_code == 0 else 0
            
            ret_code, output, _ = run_command(
                f"cat /sys/class/net/{tunnel.interface_name}/statistics/tx_bytes", 
                check=False
            )
            tx_bytes = int(output.strip()) if ret_code == 0 else 0
            
            metrics = {
                "tunnel_id": tunnel_id,
                "timestamp": datetime.now().isoformat(),
                "interface_name": tunnel.interface_name,
                "bytes_received": rx_bytes,
                "bytes_sent": tx_bytes,
                "status": "active" if rx_bytes > 0 or tx_bytes > 0 else "inactive"
            }
            
            return {
                "success": True,
                "message": f"Metrics for tunnel {tunnel_id}",
                "data": metrics
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get metrics: {e}"
            )
    
    @router.get("/health-check")
    async def comprehensive_health_check():
        """Comprehensive system health check"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "components": {}
            }
            
            # Check tunnel manager
            try:
                tunnels = manager.list_tunnels()
                health_status["components"]["tunnel_manager"] = {
                    "status": "healthy",
                    "total_tunnels": len(tunnels),
                    "active_tunnels": sum(1 for t in tunnels.values() 
                                         if t.get('status', {}).get('status') == 'up')
                }
            except Exception as e:
                health_status["components"]["tunnel_manager"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
            
            # Check orchestrator
            try:
                health_status["components"]["orchestrator"] = {
                    "status": "healthy",
                    "total_nodes": len(orchestrator.nodes)
                }
            except Exception as e:
                health_status["components"]["orchestrator"] = {
                    "status": "unhealthy", 
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"
            
            # Check system requirements
            from .utils import run_command
            requirements_status = []
            
            for cmd in ["ip", "bridge"]:
                ret_code, _, _ = run_command(f"which {cmd}", check=False)
                requirements_status.append({
                    "command": cmd,
                    "available": ret_code == 0
                })
            
            health_status["components"]["system_requirements"] = {
                "status": "healthy" if all(r["available"] for r in requirements_status) else "unhealthy",
                "requirements": requirements_status
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Health check failed: {e}"
            )
    
    @router.post("/backup-configuration")
    async def backup_configuration():
        """Create backup of current configuration"""
        try:
            import shutil
            from pathlib import Path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(f"./backups/{timestamp}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup tunnel configuration
            if manager.config_path.exists():
                shutil.copy2(manager.config_path, backup_dir / "tunnels.yaml")
            
            # Backup node configuration
            if orchestrator.config_path.exists():
                shutil.copy2(orchestrator.config_path, backup_dir / "nodes.yaml")
            
            return {
                "success": True,
                "message": f"Configuration backed up to {backup_dir}",
                "backup_path": str(backup_dir)
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Backup failed: {e}"
            )
    
    @router.post("/validate-configuration")
    async def validate_configuration():
        """Validate current system configuration"""
        try:
            validation_results = {
                "overall_valid": True,
                "tunnel_validation": [],
                "system_validation": []
            }
            
            # Validate tunnels
            for tunnel_id, tunnel in manager.tunnels.items():
                tunnel_status = {
                    "tunnel_id": tunnel_id,
                    "valid": True,
                    "issues": []
                }
                
                # Check VNI range
                if not (4096 <= tunnel.vni <= 16777215):
                    tunnel_status["valid"] = False
                    tunnel_status["issues"].append(f"Invalid VNI: {tunnel.vni}")
                
                # Check IP addresses
                try:
                    import ipaddress
                    ipaddress.ip_address(tunnel.local_ip)
                    ipaddress.ip_address(tunnel.remote_ip)
                except:
                    tunnel_status["valid"] = False
                    tunnel_status["issues"].append("Invalid IP addresses")
                
                validation_results["tunnel_validation"].append(tunnel_status)
                if not tunnel_status["valid"]:
                    validation_results["overall_valid"] = False
            
            # Validate system requirements
            from .utils import run_command
            for cmd in ["ip", "bridge"]:
                ret_code, _, _ = run_command(f"which {cmd}", check=False)
                if ret_code != 0:
                    validation_results["system_validation"].append({
                        "component": cmd,
                        "valid": False,
                        "issue": f"Command {cmd} not found"
                    })
                    validation_results["overall_valid"] = False
            
            return {
                "success": True,
                "message": "Configuration validation completed",
                "data": validation_results
            }
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Configuration validation failed: {e}"
            )
    
    return router
