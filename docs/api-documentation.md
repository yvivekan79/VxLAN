
# VxLAN Tunnel Management API Documentation

## Overview

The VxLAN Tunnel Management API provides comprehensive RESTful endpoints for managing VxLAN tunnels, network topologies, and distributed infrastructure. Built with FastAPI, it includes automatic OpenAPI documentation and supports both basic and advanced operations.

**Base URL:** `http://your-replit-url/`  
**API Version:** v1  
**Documentation:** `/docs` (Swagger UI) or `/redoc` (ReDoc)

## Authentication

Currently, the API does not require authentication. In production deployments, consider implementing JWT tokens or API keys.

## Response Format

All API responses follow a consistent format:

```json
{
  "success": boolean,
  "message": "string",
  "data": object | null
}
```

## Core Endpoints

### Tunnel Management

#### List All Tunnels
```http
GET /api/v1/tunnels
```

**Response:**
```json
{
  "vxlan1001": {
    "tunnel_id": "vxlan1001",
    "vni": 1001,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10",
    "interface_name": "vxlan1001",
    "bridge_name": "br-lan",
    "status": {
      "status": "up",
      "interface_exists": true
    }
  }
}
```

#### Get Specific Tunnel
```http
GET /api/v1/tunnels/{tunnel_id}
```

**Parameters:**
- `tunnel_id` (path): Tunnel identifier

#### Create Tunnel
```http
POST /api/v1/tunnels
```

**Request Body:**
```json
{
  "vni": 1001,
  "local_ip": "192.168.1.10",
  "remote_ip": "192.168.2.10",
  "interface_name": "vxlan1001",
  "bridge_name": "br-lan",
  "physical_interface": "eth0",
  "mtu": 1450,
  "port": 4789,
  "label": "Site A to Site B",
  "encryption": "none",
  "bridge_ip": "10.0.1.1",
  "bridge_netmask": "24"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tunnel vxlan1001 created successfully",
  "data": {
    "tunnel_id": "vxlan1001"
  }
}
```

#### Update Tunnel
```http
PUT /api/v1/tunnels/{tunnel_id}
```

#### Delete Tunnel
```http
DELETE /api/v1/tunnels/{tunnel_id}
```

### Topology Management

#### Create Network Topology
```http
POST /api/v1/topology
```

**Request Body:**
```json
{
  "topology_type": "hub-spoke",
  "nodes": {
    "hub": {
      "ip": "192.168.1.10",
      "vni_base": 1000
    },
    "spokes": [
      {"ip": "192.168.2.10", "name": "site-b"},
      {"ip": "192.168.3.10", "name": "site-c"}
    ]
  }
}
```

#### Plan Topology (Dry Run)
```http
GET /api/v1/topology/plan/{topology_type}?nodes={json_string}
```

### Orchestrator Management

#### List Remote Nodes
```http
GET /api/v1/nodes
```

#### Add Remote Node
```http
POST /api/v1/nodes
```

**Request Body:**
```json
{
  "node_id": "site-a",
  "hostname": "192.168.1.10",
  "connection_type": "ssh",
  "username": "admin",
  "ssh_key_path": "/path/to/key"
}
```

#### Get Node Status
```http
GET /api/v1/nodes/{node_id}/status
```

#### Create Tunnel on Remote Node
```http
POST /api/v1/nodes/{node_id}/tunnels
```

#### Deploy Topology Across Nodes
```http
POST /api/v1/orchestrator/deploy
```

**Request Body:**
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

## Advanced Endpoints

### Bulk Operations
```http
POST /api/v1/advanced/bulk-operations
```

**Request Body:**
```json
{
  "operation": "create",
  "tunnels": [
    {
      "vni": 1001,
      "local_ip": "192.168.1.10",
      "remote_ip": "192.168.2.10",
      "interface_name": "vxlan1001",
      "bridge_name": "br-lan"
    }
  ]
}
```

### Network Metrics
```http
GET /api/v1/advanced/network-metrics/{tunnel_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Metrics for tunnel vxlan1001",
  "data": {
    "tunnel_id": "vxlan1001",
    "timestamp": "2024-01-01T10:00:00Z",
    "interface_name": "vxlan1001",
    "bytes_received": 1024000,
    "bytes_sent": 2048000,
    "status": "active"
  }
}
```

### Health Check
```http
GET /api/v1/advanced/health-check
```

### Configuration Backup
```http
POST /api/v1/advanced/backup-configuration
```

### Configuration Validation
```http
POST /api/v1/advanced/validate-configuration
```

## System Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "vxlan-manager"
}
```

### System Status
```http
GET /api/v1/status
```

### System Configuration
```http
GET /api/v1/config
```

### State Recovery
```http
POST /api/v1/recover
```

### Tunnel Logs
```http
GET /api/v1/tunnels/{tunnel_id}/logs?lines=100
```

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

## Data Models

### VxLAN Tunnel
```json
{
  "vni": "integer (4096-16777215)",
  "local_ip": "string (IPv4 address)",
  "remote_ip": "string (IPv4 address)",
  "interface_name": "string",
  "bridge_name": "string",
  "physical_interface": "string (default: eth0)",
  "mtu": "integer (1280-9000, default: 1450)",
  "port": "integer (1-65535, default: 4789)",
  "label": "string (optional)",
  "encryption": "string (none|psk|ikev2)",
  "psk_key": "string (optional)",
  "bridge_ip": "string (optional)",
  "bridge_netmask": "string (optional)",
  "tunnel_ip": "string (optional)",
  "tunnel_netmask": "string (optional)"
}
```

### Node Configuration
```json
{
  "node_id": "string",
  "hostname": "string",
  "connection_type": "string (ssh|http)",
  "port": "integer (optional)",
  "username": "string (for SSH)",
  "ssh_key_path": "string (for SSH)",
  "api_port": "integer (for HTTP)"
}
```

## Example Usage

### Creating a Hub-Spoke Topology

1. **Create Hub Node:**
```bash
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1001,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10",
    "bridge_ip": "10.0.1.1",
    "bridge_netmask": "24",
    "label": "Hub to Spoke 1"
  }'
```

2. **Create Spoke Connections:**
```bash
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1002,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.3.10",
    "bridge_ip": "10.0.2.1",
    "bridge_netmask": "24",
    "label": "Hub to Spoke 2"
  }'
```

### Using Orchestrator for Multi-Node Deployment

1. **Add Remote Nodes:**
```bash
curl -X POST http://your-replit-url/api/v1/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "site-a",
    "hostname": "192.168.1.10",
    "connection_type": "ssh",
    "username": "admin"
  }'
```

2. **Deploy Topology:**
```bash
curl -X POST http://your-replit-url/api/v1/orchestrator/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "topology_type": "hub-spoke",
    "node_configs": {
      "hub": {"ip": "192.168.1.10"},
      "spokes": [
        {"ip": "192.168.2.10", "name": "site-b"},
        {"ip": "192.168.3.10", "name": "site-c"}
      ]
    }
  }'
```

## SDKs and Client Libraries

### Python Client Example
```python
import requests

class VxLANClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def create_tunnel(self, tunnel_config):
        response = requests.post(
            f"{self.base_url}/api/v1/tunnels",
            json=tunnel_config
        )
        return response.json()
    
    def list_tunnels(self):
        response = requests.get(f"{self.base_url}/api/v1/tunnels")
        return response.json()

# Usage
client = VxLANClient("http://your-replit-url")
tunnels = client.list_tunnels()
```

### JavaScript Client Example
```javascript
class VxLANClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async createTunnel(tunnelConfig) {
        const response = await fetch(`${this.baseUrl}/api/v1/tunnels`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(tunnelConfig)
        });
        return response.json();
    }
    
    async listTunnels() {
        const response = await fetch(`${this.baseUrl}/api/v1/tunnels`);
        return response.json();
    }
}

// Usage
const client = new VxLANClient('http://your-replit-url');
const tunnels = await client.listTunnels();
```

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting based on IP address or API key.

## Changelog

### Version 1.0.0
- Initial API release
- Basic tunnel CRUD operations
- Topology management
- Orchestrator integration
- Advanced bulk operations
- Metrics and monitoring endpoints
