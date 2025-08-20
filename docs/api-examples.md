# VxLAN API Usage Examples

This document provides practical examples for using the VxLAN Tunnel Management API.

## Quick Start Examples

### 1. Basic Point-to-Point Tunnel

Create a simple Layer 2 tunnel between two sites:

```bash
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1001,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10",
    "bridge_name": "br-lan",
    "label": "Site A to Site B"
  }'
```

### 2. Layer 3 Routed Tunnel

Create a tunnel with IP routing capabilities:

```bash
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1002,
    "local_ip": "203.0.113.10",
    "remote_ip": "198.51.100.20",
    "bridge_name": "br-lan",
    "bridge_ip": "10.0.1.1",
    "bridge_netmask": "24",
    "label": "Routed connection with 10.0.1.0/24 subnet"
  }'
```

## Network Topology Examples

### Hub-Spoke Topology

Deploy a hub-spoke network with one central hub and multiple spokes:

```bash
curl -X POST http://your-replit-url/api/v1/topology \
  -H "Content-Type: application/json" \
  -d '{
    "topology_type": "hub-spoke",
    "nodes": {
      "hub": {
        "ip": "192.168.1.10",
        "vni_base": 1000,
        "bridge_ip": "10.0.0.1",
        "bridge_netmask": "16"
      },
      "spokes": [
        {
          "ip": "192.168.2.10",
          "name": "branch-office-1",
          "bridge_ip": "10.0.1.1",
          "bridge_netmask": "24"
        },
        {
          "ip": "192.168.3.10", 
          "name": "branch-office-2",
          "bridge_ip": "10.0.2.1",
          "bridge_netmask": "24"
        },
        {
          "ip": "192.168.4.10",
          "name": "data-center",
          "bridge_ip": "10.0.3.1", 
          "bridge_netmask": "24"
        }
      ]
    }
  }'
```

### Full-Mesh Topology

Create complete connectivity between all sites:

```bash
curl -X POST http://your-replit-url/api/v1/topology \
  -H "Content-Type: application/json" \
  -d '{
    "topology_type": "full-mesh",
    "nodes": {
      "site-a": {"ip": "192.168.1.10", "subnet": "10.1.0.0/24"},
      "site-b": {"ip": "192.168.2.10", "subnet": "10.2.0.0/24"},
      "site-c": {"ip": "192.168.3.10", "subnet": "10.3.0.0/24"},
      "site-d": {"ip": "192.168.4.10", "subnet": "10.4.0.0/24"}
    }
  }'
```

## Multi-Node Orchestrator Examples

### Adding Remote Nodes

```bash
# Add SSH-based node
curl -X POST http://your-replit-url/api/v1/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "remote-site-1",
    "hostname": "203.0.113.10",
    "connection_type": "ssh",
    "username": "vxlan-admin",
    "ssh_key_path": "/home/admin/.ssh/id_rsa"
  }'

# Add HTTP API-based node
curl -X POST http://your-replit-url/api/v1/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "remote-site-2", 
    "hostname": "198.51.100.20",
    "connection_type": "http",
    "api_port": 8001
  }'
```

### Deploy Distributed Topology

```bash
curl -X POST http://your-replit-url/api/v1/orchestrator/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "topology_type": "hub-spoke",
    "node_configs": {
      "hub": {
        "node_id": "headquarters",
        "ip": "203.0.113.10",
        "subnets": ["10.0.0.0/16"]
      },
      "spokes": [
        {
          "node_id": "remote-site-1",
          "ip": "198.51.100.20",
          "subnets": ["10.1.0.0/24"]
        },
        {
          "node_id": "remote-site-2", 
          "ip": "203.0.113.30",
          "subnets": ["10.2.0.0/24"]
        }
      ]
    }
  }'
```

## Advanced Operations

### Bulk Tunnel Management

Create multiple tunnels in a single operation:

```bash
curl -X POST http://your-replit-url/api/v1/advanced/bulk-operations \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "create",
    "tunnels": [
      {
        "vni": 2001,
        "local_ip": "192.168.1.10",
        "remote_ip": "192.168.2.10", 
        "bridge_name": "br-dmz",
        "bridge_ip": "172.16.1.1",
        "bridge_netmask": "24",
        "label": "DMZ Network"
      },
      {
        "vni": 2002,
        "local_ip": "192.168.1.10",
        "remote_ip": "192.168.3.10",
        "bridge_name": "br-guest",
        "bridge_ip": "172.16.2.1", 
        "bridge_netmask": "24",
        "label": "Guest Network"
      },
      {
        "vni": 2003,
        "local_ip": "192.168.1.10",
        "remote_ip": "192.168.4.10",
        "bridge_name": "br-mgmt",
        "bridge_ip": "172.16.3.1",
        "bridge_netmask": "24", 
        "label": "Management Network"
      }
    ]
  }'
```

### Network Monitoring

Get tunnel metrics and statistics:

```bash
# Get metrics for a specific tunnel
curl http://your-replit-url/api/v1/advanced/network-metrics/vxlan1001

# Comprehensive system health check
curl http://your-replit-url/api/v1/advanced/health-check

# Get system status
curl http://your-replit-url/api/v1/status
```

## Security Examples

### Encrypted Tunnels

Create tunnels with PSK encryption:

```bash
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 3001,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10",
    "bridge_name": "br-secure",
    "encryption": "psk",
    "psk_key": "your-secure-pre-shared-key-here",
    "label": "Encrypted tunnel with PSK"
  }'
```

## Error Handling Examples

### Handling Common Errors

```bash
# Invalid VNI (should be 4096-16777215)
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 100,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10"
  }'
# Returns: 400 Bad Request

# Duplicate tunnel
curl -X POST http://your-replit-url/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1001,
    "local_ip": "192.168.1.10",
    "remote_ip": "192.168.2.10"
  }'
# Returns existing tunnel if configuration matches
```

## Integration Examples

### Python SDK Usage

```python
import requests
import json

class VxLANClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def create_tunnel(self, **kwargs):
        response = requests.post(
            f"{self.base_url}/api/v1/tunnels",
            json=kwargs,
            headers={'Content-Type': 'application/json'}
        )
        return response.json()

    def list_tunnels(self):
        response = requests.get(f"{self.base_url}/api/v1/tunnels")
        return response.json()

    def deploy_hub_spoke(self, hub_config, spoke_configs):
        topology_config = {
            "topology_type": "hub-spoke",
            "nodes": {
                "hub": hub_config,
                "spokes": spoke_configs
            }
        }
        response = requests.post(
            f"{self.base_url}/api/v1/topology",
            json=topology_config
        )
        return response.json()

# Usage example
client = VxLANClient("http://your-replit-url")

# Create a simple tunnel
result = client.create_tunnel(
    vni=1001,
    local_ip="192.168.1.10",
    remote_ip="192.168.2.10",
    bridge_ip="10.0.1.1",
    bridge_netmask="24",
    label="Python SDK tunnel"
)

print(json.dumps(result, indent=2))
```

### Bash Script Automation

```bash
#!/bin/bash

API_BASE="http://localhost:8000"

# Function to create tunnel
create_tunnel() {
    local vni=$1
    local local_ip=$2
    local remote_ip=$3
    local label=$4

    curl -s -X POST "$API_BASE/api/v1/tunnels" \
        -H "Content-Type: application/json" \
        -d "{
            \"vni\": $vni,
            \"local_ip\": \"$local_ip\",
            \"remote_ip\": \"$remote_ip\",
            \"bridge_name\": \"br-lan\",
            \"label\": \"$label\"
        }" | jq '.'
}

# Function to check tunnel status
check_tunnel() {
    local tunnel_id=$1
    curl -s "$API_BASE/api/v1/tunnels/$tunnel_id" | jq '.status'
}

# Create multiple tunnels
create_tunnel 1001 "192.168.1.10" "192.168.2.10" "Branch Office 1"
create_tunnel 1002 "192.168.1.10" "192.168.3.10" "Branch Office 2"
create_tunnel 1003 "192.168.1.10" "192.168.4.10" "Data Center"

# Check system health
echo "System Health:"
curl -s "$API_BASE/health" | jq '.'
```

## Testing and Validation

### Validate Configuration

```bash
# Validate current system configuration
curl -X POST http://your-replit-url/api/v1/advanced/validate-configuration
```

### Backup Configuration

```bash
# Create configuration backup
curl -X POST http://your-replit-url/api/v1/advanced/backup-configuration
```

### Recovery Operations

```bash
# Recover tunnel state from configuration
curl -X POST http://your-replit-url/api/v1/recover
```

These examples provide a comprehensive guide for using the VxLAN Tunnel Management API in various scenarios, from simple point-to-point connections to complex multi-node topologies.