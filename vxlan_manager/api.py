"""
REST API interface for VxLAN tunnel management
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import json

from .core import VxLANManager, VxLANTunnel
from .topology import TopologyManager
from .logger import get_logger

logger = get_logger(__name__)

# Pydantic models for API
class TunnelCreateRequest(BaseModel):
    vni: int = Field(..., ge=4096, le=16777215, description="VxLAN Network Identifier")
    local_ip: str = Field(..., description="Local endpoint IP address")
    remote_ip: str = Field(..., description="Remote endpoint IP address")
    interface_name: Optional[str] = Field(None, description="VxLAN interface name")
    bridge_name: str = Field("br-lan", description="Bridge name")
    physical_interface: str = Field("eth0", description="Physical interface")
    mtu: int = Field(1450, ge=1280, le=9000, description="MTU size")
    port: int = Field(4789, ge=1, le=65535, description="VxLAN port")
    label: str = Field("", description="Optional label for the tunnel")
    encryption: str = Field("none", description="Encryption type")
    psk_key: Optional[str] = Field(None, description="Pre-shared key for PSK encryption")
    bridge_ip: Optional[str] = Field(None, description="IP address for the bridge")
    bridge_netmask: Optional[str] = Field(None, description="Netmask for bridge IP")
    tunnel_ip: Optional[str] = Field(None, description="IP address for tunnel interface")
    tunnel_netmask: Optional[str] = Field(None, description="Netmask for tunnel IP")

    @validator('encryption')
    def validate_encryption(cls, v):
        if v not in ['none', 'psk', 'ikev2']:
            raise ValueError('encryption must be one of: none, psk, ikev2')
        return v

class TunnelResponse(BaseModel):
    tunnel_id: str
    vni: int
    local_ip: str
    remote_ip: str
    interface_name: str
    bridge_name: str
    physical_interface: str
    mtu: int
    port: int
    label: str
    encryption: str
    psk_key: Optional[str]
    status: Optional[Dict[str, Any]]

class TopologyCreateRequest(BaseModel):
    topology_type: str = Field(..., description="Topology type")
    nodes: Dict[str, Dict[str, Any]] = Field(..., description="Node configuration")

    @validator('topology_type')
    def validate_topology_type(cls, v):
        if v not in ['hub-spoke', 'full-mesh', 'partial-mesh']:
            raise ValueError('topology_type must be one of: hub-spoke, full-mesh, partial-mesh')
        return v

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

def create_app(config_path: str = "./config/tunnels.yaml") -> FastAPI:
    """Create FastAPI application"""

    app = FastAPI(
        title="VxLAN Tunnel Management API",
        description="""
        ## VxLAN Tunnel Management System
        
        A comprehensive REST API for managing VxLAN (Virtual Extensible LAN) tunnels and network topologies.
        
        ### Features
        - **Tunnel Management**: Create, update, delete, and monitor VxLAN tunnels
        - **Topology Deployment**: Support for hub-spoke, full-mesh, and partial-mesh topologies
        - **Orchestrator**: Multi-node coordination for distributed deployments
        - **Layer 3 Support**: IP configuration for tunnel interfaces and bridges
        - **Monitoring**: Real-time metrics and health checks
        - **Bulk Operations**: Efficient batch processing of tunnel operations
        
        ### Supported Topologies
        - **Point-to-Point**: Direct tunnel between two sites
        - **Hub-Spoke**: Central hub with multiple spoke connections
        - **Full-Mesh**: Complete connectivity between all nodes
        - **Partial-Mesh**: Selective connectivity based on requirements
        
        ### Network Layers
        - **Layer 2**: Bridge-based connectivity for switching
        - **Layer 3**: IP-routed connectivity with subnet configuration
        
        ### Quick Start
        1. Use `/api/v1/tunnels` for basic tunnel operations
        2. Use `/api/v1/topology` for network topology deployment
        3. Use `/api/v1/orchestrator/deploy` for multi-node deployments
        4. Check `/health` for system status
        
        ### Authentication
        Currently no authentication required. Consider implementing API keys or JWT tokens for production.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        contact={
            "name": "VxLAN Management System",
            "url": "https://github.com/your-org/vxlan-management",
            "email": "support@example.com"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": "/",
                "description": "Current server"
            }
        ],
        tags_metadata=[
            {
                "name": "tunnels",
                "description": "VxLAN tunnel CRUD operations",
            },
            {
                "name": "topology",
                "description": "Network topology management",
            },
            {
                "name": "orchestrator", 
                "description": "Multi-node coordination and deployment",
            },
            {
                "name": "system",
                "description": "System status and configuration",
            },
            {
                "name": "advanced",
                "description": "Advanced operations and bulk processing",
            }
        ]
    )

    # Initialize manager
    manager = VxLANManager(config_path)
    topology_manager = TopologyManager(manager)

    # Initialize orchestrator
    from .orchestrator import VxLANOrchestrator
    orchestrator = VxLANOrchestrator()

    # Include advanced API router
    from .api_advanced import create_advanced_router
    advanced_router = create_advanced_router(manager, orchestrator)
    app.include_router(advanced_router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "Internal server error", "data": None}
        )

    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "service": "VxLAN Tunnel Management API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "api_base": "/api/v1",
                "tunnels": "/api/v1/tunnels",
                "topology": "/api/v1/topology"
            }
        }

    @app.get(
        "/health",
        tags=["system"],
        summary="System health check",
        description="Check the overall health status of the VxLAN management system.",
        responses={
            200: {
                "description": "System is healthy",
                "content": {
                    "application/json": {
                        "example": {
                            "status": "healthy",
                            "service": "vxlan-manager"
                        }
                    }
                }
            }
        }
    )
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "vxlan-manager"}

    @app.get(
        "/api/v1/tunnels", 
        response_model=Dict[str, TunnelResponse],
        tags=["tunnels"],
        summary="List all VxLAN tunnels",
        description="Retrieve a comprehensive list of all configured VxLAN tunnels with their current status and configuration details.",
        responses={
            200: {
                "description": "Successfully retrieved tunnels",
                "content": {
                    "application/json": {
                        "example": {
                            "vxlan1001": {
                                "tunnel_id": "vxlan1001",
                                "vni": 1001,
                                "local_ip": "192.168.1.10",
                                "remote_ip": "192.168.2.10",
                                "interface_name": "vxlan1001",
                                "bridge_name": "br-lan",
                                "status": {
                                    "status": "up",
                                    "interface_exists": True
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    async def list_tunnels():
        """List all VxLAN tunnels with status information"""
        try:
            tunnels = manager.list_tunnels()
            return tunnels
        except Exception as e:
            logger.error(f"Failed to list tunnels: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list tunnels: {e}"
            )

    @app.get("/api/v1/tunnels/{tunnel_id}", response_model=TunnelResponse)
    async def get_tunnel(tunnel_id: str):
        """Get specific tunnel information"""
        try:
            tunnels = manager.list_tunnels()
            if tunnel_id not in tunnels:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tunnel {tunnel_id} not found"
                )
            return tunnels[tunnel_id]
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get tunnel {tunnel_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tunnel: {e}"
            )

    @app.post(
        "/api/v1/tunnels", 
        response_model=APIResponse,
        tags=["tunnels"],
        summary="Create a new VxLAN tunnel",
        description="""
        Create a new VxLAN tunnel with comprehensive configuration options.
        
        **Layer 2 Configuration:**
        - Specify VNI (4096-16777215)
        - Configure local and remote IP endpoints
        - Set bridge and interface names
        
        **Layer 3 Configuration (Optional):**
        - Configure bridge_ip and bridge_netmask for routed connectivity
        - Alternatively, use tunnel_ip and tunnel_netmask for direct interface IP
        
        **Security Options:**
        - encryption: none (default), psk, ikev2
        - psk_key: Pre-shared key for PSK encryption
        """,
        responses={
            200: {
                "description": "Tunnel created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "message": "Tunnel vxlan1001 created successfully",
                            "data": {"tunnel_id": "vxlan1001"}
                        }
                    }
                }
            },
            400: {"description": "Invalid tunnel configuration"},
            500: {"description": "Failed to create tunnel"}
        }
    )
    async def create_tunnel(
        request: TunnelCreateRequest = {
            "vni": 1001,
            "local_ip": "192.168.1.10", 
            "remote_ip": "192.168.2.10",
            "bridge_name": "br-lan",
            "bridge_ip": "10.0.1.1",
            "bridge_netmask": "24",
            "label": "Site A to Site B connection"
        }
    ):
        """Create a new VxLAN tunnel with Layer 2/3 configuration"""
        try:
            # Generate interface name if not provided
            interface_name = request.interface_name or f"vxlan{request.vni}"

            # Create tunnel object
            tunnel = VxLANTunnel(
                vni=request.vni,
                local_ip=request.local_ip,
                remote_ip=request.remote_ip,
                interface_name=interface_name,
                bridge_name=request.bridge_name,
                physical_interface=request.physical_interface,
                mtu=request.mtu,
                port=request.port,
                label=request.label,
                encryption=request.encryption,
                psk_key=request.psk_key,
                bridge_ip=request.bridge_ip,
                bridge_netmask=request.bridge_netmask,
                tunnel_ip=request.tunnel_ip,
                tunnel_netmask=request.tunnel_netmask
            )

            tunnel_id = manager.create_tunnel(tunnel)

            return APIResponse(
                success=True,
                message=f"Tunnel {tunnel_id} created successfully",
                data={"tunnel_id": tunnel_id}
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create tunnel: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create tunnel: {e}"
            )

    @app.delete("/api/v1/tunnels/{tunnel_id}", response_model=APIResponse)
    async def delete_tunnel(tunnel_id: str):
        """Delete a VxLAN tunnel"""
        try:
            manager.delete_tunnel(tunnel_id)
            return APIResponse(
                success=True,
                message=f"Tunnel {tunnel_id} deleted successfully"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to delete tunnel {tunnel_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete tunnel: {e}"
            )

    @app.post(
        "/api/v1/topology", 
        response_model=APIResponse,
        tags=["topology"],
        summary="Create network topology",
        description="""
        Deploy a complete network topology with multiple tunnels.
        
        **Supported Topologies:**
        - **hub-spoke**: Central hub with multiple spoke connections
        - **full-mesh**: Complete connectivity between all nodes
        - **partial-mesh**: Selective connectivity based on requirements
        
        **Example Hub-Spoke Configuration:**
        ```json
        {
          "topology_type": "hub-spoke",
          "nodes": {
            "hub": {"ip": "192.168.1.10", "vni_base": 1000},
            "spokes": [
              {"ip": "192.168.2.10", "name": "site-b"},
              {"ip": "192.168.3.10", "name": "site-c"}
            ]
          }
        }
        ```
        """,
        responses={
            200: {
                "description": "Topology created successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "message": "Created hub-spoke topology with 2 tunnels",
                            "data": {
                                "vxlan1001": "hub-to-spoke1",
                                "vxlan1002": "hub-to-spoke2"
                            }
                        }
                    }
                }
            }
        }
    )
    async def create_topology(request: TopologyCreateRequest):
        """Create and deploy a network topology"""
        try:
            result = topology_manager.create_topology(
                request.topology_type, 
                request.nodes
            )

            return APIResponse(
                success=True,
                message=f"Created {request.topology_type} topology with {len(result)} tunnels",
                data=result
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create topology: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create topology: {e}"
            )

    @app.get("/api/v1/topology/plan/{topology_type}")
    async def plan_topology(topology_type: str, nodes: str):
        """Plan topology without creating tunnels (dry run)"""
        try:
            import json
            nodes_data = json.loads(nodes)

            result = topology_manager.plan_topology(topology_type, nodes_data)

            return APIResponse(
                success=True,
                message=f"Topology plan for {topology_type}",
                data=result
            )

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to plan topology: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to plan topology: {e}"
            )

    @app.post("/api/v1/recover", response_model=APIResponse)
    async def recover_state():
        """Recover tunnel state from configuration"""
        try:
            manager.recover_state()
            return APIResponse(
                success=True,
                message="State recovery completed"
            )
        except Exception as e:
            logger.error(f"Failed to recover state: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to recover state: {e}"
            )

    @app.get("/api/v1/status")
    async def system_status():
        """Get system status"""
        try:
            tunnels = manager.list_tunnels()
            status = {
                'total_tunnels': len(tunnels),
                'active_tunnels': sum(1 for t in tunnels.values() 
                                     if t.get('status', {}).get('status') == 'up'),
                'configuration_path': str(manager.config_path),
                'service_status': 'running'
            }

            return APIResponse(
                success=True,
                message="System status retrieved",
                data=status
            )

        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get status: {e}"
            )

    # Orchestrator endpoints (using the one initialized above)
    from .orchestrator import RemoteNode

    @app.get("/api/v1/nodes")
    async def list_nodes():
        """List all remote nodes"""
        try:
            nodes = {node_id: {
                'node_id': node.node_id,
                'hostname': node.hostname,
                'connection_type': node.connection_type,
                'port': node.port,
                'username': node.username
            } for node_id, node in orchestrator.nodes.items()}

            return APIResponse(
                success=True,
                message="Nodes retrieved successfully",
                data=nodes
            )
        except Exception as e:
            logger.error(f"Failed to list nodes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list nodes: {e}"
            )

    @app.post("/api/v1/nodes")
    async def add_node(node_data: dict):
        """Add a new remote node"""
        try:
            node = RemoteNode(**node_data)
            orchestrator.add_node(node)

            return APIResponse(
                success=True,
                message=f"Node {node.node_id} added successfully",
                data={'node_id': node.node_id}
            )
        except Exception as e:
            logger.error(f"Failed to add node: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add node: {e}"
            )

    @app.get("/api/v1/nodes/{node_id}/status")
    async def get_node_status(node_id: str):
        """Get status of a specific node"""
        try:
            status_result = await orchestrator.get_node_status(node_id)
            return APIResponse(
                success=True,
                message=f"Node {node_id} status retrieved",
                data=status_result
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to get node status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get node status: {e}"
            )

    @app.post("/api/v1/nodes/{node_id}/tunnels")
    async def create_tunnel_on_node(node_id: str, request: TunnelCreateRequest):
        """Create tunnel on specific remote node"""
        try:
            interface_name = request.interface_name or f"vxlan{request.vni}"

            tunnel = VxLANTunnel(
                vni=request.vni,
                local_ip=request.local_ip,
                remote_ip=request.remote_ip,
                interface_name=interface_name,
                bridge_name=request.bridge_name,
                physical_interface=request.physical_interface,
                mtu=request.mtu,
                port=request.port,
                label=request.label,
                encryption=request.encryption,
                psk_key=request.psk_key,
                bridge_ip=request.bridge_ip,
                bridge_netmask=request.bridge_netmask,
                tunnel_ip=request.tunnel_ip,
                tunnel_netmask=request.tunnel_netmask
            )

            result = await orchestrator.create_tunnel_on_node(node_id, tunnel)

            return APIResponse(
                success=True,
                message=f"Tunnel created on node {node_id}",
                data=result
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to create tunnel on node: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create tunnel on node: {e}"
            )

    @app.delete("/api/v1/nodes/{node_id}/tunnels/{interface_name}")
    async def delete_tunnel_on_node(node_id: str, interface_name: str):
        """Delete tunnel on specific remote node"""
        try:
            result = await orchestrator.delete_tunnel_on_node(node_id, interface_name)

            return APIResponse(
                success=True,
                message=f"Tunnel {interface_name} deleted on node {node_id}",
                data=result
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to delete tunnel on node: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete tunnel on node: {e}"
            )

    @app.post(
        "/api/v1/orchestrator/deploy",
        tags=["orchestrator"],
        summary="Deploy topology across multiple nodes",
        description="""
        Deploy a network topology across multiple remote nodes using the orchestrator.
        
        This endpoint coordinates tunnel creation across distributed infrastructure,
        handling both SSH and HTTP-based node connections.
        
        **Example Request:**
        ```json
        {
          "topology_type": "full-mesh",
          "node_configs": {
            "site-a": {"ip": "192.168.1.10"},
            "site-b": {"ip": "192.168.2.10"},
            "site-c": {"ip": "192.168.3.10"}
          }
        }
        ```
        """,
        responses={
            200: {
                "description": "Topology deployed successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "success": True,
                            "message": "Topology full-mesh deployed successfully",
                            "data": {
                                "deployed_tunnels": 6,
                                "affected_nodes": 3
                            }
                        }
                    }
                }
            }
        }
    )
    async def deploy_topology_orchestrator(request: dict):
        """Deploy topology across multiple nodes using orchestrator"""
        try:
            topology_type = request.get('topology_type')
            node_configs = request.get('node_configs', {})

            result = await orchestrator.deploy_topology(topology_type, node_configs)

            return APIResponse(
                success=True,
                message=f"Topology {topology_type} deployed successfully",
                data=result
            )
        except Exception as e:
            logger.error(f"Failed to deploy topology: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deploy topology: {e}"
            )

    @app.put("/api/v1/tunnels/{tunnel_id}")
    async def update_tunnel(tunnel_id: str, request: TunnelCreateRequest):
        """Update an existing tunnel"""
        try:
            # Delete existing tunnel
            manager.delete_tunnel(tunnel_id)

            # Create new tunnel with updated configuration
            interface_name = request.interface_name or f"vxlan{request.vni}"

            tunnel = VxLANTunnel(
                vni=request.vni,
                local_ip=request.local_ip,
                remote_ip=request.remote_ip,
                interface_name=interface_name,
                bridge_name=request.bridge_name,
                physical_interface=request.physical_interface,
                mtu=request.mtu,
                port=request.port,
                label=request.label,
                encryption=request.encryption,
                psk_key=request.psk_key,
                bridge_ip=request.bridge_ip,
                bridge_netmask=request.bridge_netmask,
                tunnel_ip=request.tunnel_ip,
                tunnel_netmask=request.tunnel_netmask
            )

            new_tunnel_id = manager.create_tunnel(tunnel, tunnel_id)

            return APIResponse(
                success=True,
                message=f"Tunnel {tunnel_id} updated successfully",
                data={"tunnel_id": new_tunnel_id}
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Failed to update tunnel: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update tunnel: {e}"
            )

    @app.get("/api/v1/config")
    async def get_configuration():
        """Get current system configuration"""
        try:
            from .config import load_app_config
            config = load_app_config()

            return APIResponse(
                success=True,
                message="Configuration retrieved",
                data=config
            )
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get configuration: {e}"
            )

    @app.get("/api/v1/tunnels/{tunnel_id}/logs")
    async def get_tunnel_logs(tunnel_id: str, lines: int = 100):
        """Get logs for a specific tunnel"""
        try:
            if tunnel_id not in manager.tunnels:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tunnel {tunnel_id} not found"
                )

            # This is a placeholder - in a real implementation, you'd read from log files
            logs = [
                f"Tunnel {tunnel_id} created successfully",
                f"Interface {manager.tunnels[tunnel_id].interface_name} is up",
                f"Bridge {manager.tunnels[tunnel_id].bridge_name} configured"
            ]

            return APIResponse(
                success=True,
                message=f"Logs for tunnel {tunnel_id}",
                data={"logs": logs[-lines:]}
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get tunnel logs: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tunnel logs: {e}"
            )

    return app