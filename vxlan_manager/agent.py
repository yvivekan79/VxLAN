
"""
Lightweight VxLAN agent for remote nodes
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import subprocess
import os

from .core import VxLANManager, VxLANTunnel
from .logger import get_logger

logger = get_logger(__name__)

class AgentTunnelRequest(BaseModel):
    vni: int
    local_ip: str
    remote_ip: str
    interface_name: str
    bridge_name: str = "br-lan"
    physical_interface: str = "eth0"
    mtu: int = 1450
    port: int = 4789

class VxLANAgent:
    """Lightweight VxLAN agent for remote management"""
    
    def __init__(self, node_id: str, config_path: str = "./config/agent.yaml"):
        self.node_id = node_id
        self.manager = VxLANManager(config_path)
        
    def create_app(self) -> FastAPI:
        """Create FastAPI application for agent"""
        app = FastAPI(
            title="VxLAN Agent",
            description="Lightweight VxLAN tunnel agent",
            version="1.0.0"
        )
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "node_id": self.node_id}
        
        @app.post("/api/v1/tunnels")
        async def create_tunnel(request: AgentTunnelRequest):
            try:
                tunnel = VxLANTunnel(
                    vni=request.vni,
                    local_ip=request.local_ip,
                    remote_ip=request.remote_ip,
                    interface_name=request.interface_name,
                    bridge_name=request.bridge_name,
                    physical_interface=request.physical_interface,
                    mtu=request.mtu,
                    port=request.port
                )
                
                tunnel_id = self.manager.create_tunnel(tunnel)
                return {"success": True, "tunnel_id": tunnel_id}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/api/v1/tunnels/{tunnel_id}")
        async def delete_tunnel(tunnel_id: str):
            try:
                self.manager.delete_tunnel(tunnel_id)
                return {"success": True, "message": f"Tunnel {tunnel_id} deleted"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/tunnels")
        async def list_tunnels():
            try:
                tunnels = self.manager.list_tunnels()
                return {"success": True, "tunnels": tunnels}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/v1/status")
        async def get_status():
            try:
                tunnels = self.manager.list_tunnels()
                return {
                    "success": True,
                    "node_id": self.node_id,
                    "tunnel_count": len(tunnels),
                    "system_info": self._get_system_info()
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/v1/execute")
        async def execute_command(command: dict):
            """Execute system command (use with caution)"""
            try:
                cmd = command.get('command')
                if not cmd:
                    raise HTTPException(status_code=400, detail="Command required")
                
                # Basic security check
                dangerous_commands = ['rm', 'del', 'format', 'mkfs']
                if any(danger in cmd.lower() for danger in dangerous_commands):
                    raise HTTPException(status_code=403, detail="Dangerous command blocked")
                
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=30
                )
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return app
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        try:
            import platform
            return {
                "hostname": platform.node(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            }
        except:
            return {"error": "Could not retrieve system info"}

def create_agent_app(node_id: str = None) -> FastAPI:
    """Create agent application"""
    if not node_id:
        import socket
        node_id = socket.gethostname()
    
    agent = VxLANAgent(node_id)
    return agent.create_app()
