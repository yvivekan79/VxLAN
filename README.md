
# VxLAN Tunnel Management System

A comprehensive VxLAN (Virtual Extensible LAN) tunnel management system for creating and managing overlay networks across distributed infrastructure. This system provides both CLI and REST API interfaces with support for multiple network topologies and enterprise-grade features.

## 🚀 Quick Start

### Start the API Server
```bash
python main.py api
```
The API will be available at `http://localhost:5000` with interactive documentation at `/docs`.

### Use the CLI
```bash
# Create a tunnel
python main.py cli tunnel create --vni 1001 --local-ip 192.168.1.10 --remote-ip 192.168.2.10

# List all tunnels
python main.py cli tunnel list

# Delete a tunnel
python main.py cli tunnel delete vxlan1001
```

## 🏗️ Architecture

### Core Components

- **VxLAN Manager (`core.py`)**: Core tunnel lifecycle management with validation and persistence
- **CLI Interface (`cli.py`)**: Command-line interface using Click framework
- **REST API (`api.py` & `api_advanced.py`)**: FastAPI-based web service with comprehensive endpoints
- **Orchestrator (`orchestrator.py`)**: Multi-node tunnel coordination via SSH/HTTP
- **Agent (`agent.py`)**: Lightweight service for remote tunnel execution

### Network Topologies Supported

- **Point-to-Point**: Direct tunnel between two sites
- **Hub-Spoke**: Central hub with multiple spoke connections
- **Full-Mesh**: Complete connectivity between all nodes
- **Partial-Mesh**: Selective connectivity based on requirements

## 📡 API Endpoints

### Basic Tunnel Management
```bash
# Create tunnel
POST /api/v1/tunnels
{
  "vni": 1001,
  "local_ip": "192.168.1.10",
  "remote_ip": "192.168.2.10",
  "interface_name": "vxlan1001",
  "bridge_name": "br-lan"
}

# List tunnels
GET /api/v1/tunnels

# Get specific tunnel
GET /api/v1/tunnels/{tunnel_id}

# Delete tunnel
DELETE /api/v1/tunnels/{tunnel_id}

# Health check
GET /health
```

### Advanced Features
```bash
# Topology management
POST /api/v1/topology/deploy
GET /api/v1/topology/status

# System information
GET /api/v1/system/info
GET /api/v1/system/interfaces

# Orchestrator operations
POST /api/v1/orchestrator/nodes
GET /api/v1/orchestrator/status
```

## 🛠️ Configuration

### Application Configuration (`config/app_config.yaml`)
```yaml
api:
  host: "0.0.0.0"
  port: 5000
  reload: true

logging:
  level: "INFO"
  file: "/var/log/gind-tunnels.log"
  format: "ipfix"

network:
  default_bridge: "br-lan"
  default_mtu: 1450
  default_port: 4789
```

### Node Configuration (`config/nodes.yaml`)
```yaml
nodes:
  site-a:
    host: "192.168.1.10"
    connection_type: "ssh"
    ssh_user: "admin"
    ssh_key: "/etc/ssh/id_rsa"
  
  site-b:
    host: "192.168.2.10"
    connection_type: "http"
    api_port: 5001
```

## 📋 Examples

### Site-to-Site Connection

**Site A Setup:**
```bash
# Create VxLAN tunnel
ip link add vxlan1001 type vxlan id 1001 local 203.0.113.10 remote 198.51.100.20 dev eth0 dstport 4789
ip link set vxlan1001 up

# Setup bridge
ip link add br-lan type bridge
ip link set br-lan up
ip link set vxlan1001 master br-lan
ip link set vxlan1001 mtu 1450
```

**Via API:**
```bash
curl -X POST http://localhost:5000/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1001,
    "local_ip": "203.0.113.10",
    "remote_ip": "198.51.100.20",
    "interface_name": "vxlan1001",
    "bridge_name": "br-lan",
    "label": "site-a-to-site-b"
  }'
```

### Orchestrator Deployment
```python
from vxlan_manager.orchestrator import VxLANOrchestrator

# Deploy hub-spoke topology
orchestrator = VxLANOrchestrator()
await orchestrator.deploy_topology("hub-spoke", {
    "hub": "site-a",
    "spokes": ["site-b", "site-c"]
})
```

## 🔧 Features

### Security
- **Encryption Support**: None, PSK, IKEv2 modes
- **Input Validation**: VNI ranges, IP addresses, interface names
- **Secure Configuration**: Protected handling of encryption keys

### Monitoring & Logging
- **IPFIX-Compliant Logging**: Structured logs for network monitoring
- **Health Checks**: System and tunnel status monitoring
- **Event Tracking**: Tunnel lifecycle events with metadata

### High Availability
- **State Recovery**: Automatic tunnel state restoration
- **Configuration Persistence**: YAML-based configuration storage
- **Error Handling**: Comprehensive error recovery and cleanup


## 📝 System Requirements

### Dependencies
- Python 3.11+
- FastAPI, Click, Pydantic, PyYAML, Uvicorn
- Linux with iproute2 tools (`ip` command)
- Root/sudo access for network interface management

### Network Requirements
- VXLAN kernel module support
- UDP port 4789 (VXLAN) open between sites
- Management ports (SSH 22 or HTTP 5001) for orchestrator access

## 🔗 Related Commands

### Verify Tunnel Status
```bash
# Check interface
ip link show vxlan1001

# Check bridge
bridge link show

# Monitor traffic
tcpdump -i vxlan1001
```

### Troubleshooting
```bash
# Check kernel module
lsmod | grep vxlan

# Verify connectivity
ping -I vxlan1001 <remote_ip>

# Check logs
tail -f /var/log/gind-tunnels.log
```

## 📊 Monitoring Integration

The system provides IPFIX-compliant structured logging for integration with network monitoring systems:

```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "event": "tunnel_create",
  "tunnel_id": "vxlan1001",
  "vni": 1001,
  "local_ip": "192.168.1.10",
  "remote_ip": "192.168.2.10"
}
```

This enables seamless integration with SIEM, network monitoring, and observability platforms.
