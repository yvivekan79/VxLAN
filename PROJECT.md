# VxLAN Tunnel Management System

A comprehensive Python-based solution for managing Virtual Extensible LAN (VxLAN) tunnels across distributed infrastructure. This system provides both CLI and REST API interfaces for creating and managing network overlay topologies.

## Features

- **Tunnel Management**: Create, delete, and monitor VxLAN tunnels with proper validation
- **Multiple Topologies**: Support for hub-spoke, full-mesh, and partial-mesh network topologies
- **CLI Interface**: Comprehensive command-line tools for tunnel operations
- **REST API**: FastAPI-based web service with automatic documentation
- **Configuration Management**: YAML-based persistent configuration storage
- **Structured Logging**: IPFIX-compliant logging with JSON output format
- **Encryption Support**: Multiple encryption options (none, PSK, IKEv2)
- **Idempotent Operations**: Safe tunnel creation and management
- **System Recovery**: Automatic state recovery and configuration validation

## Requirements

### System Requirements
- **Operating System**: Ubuntu 22.04 LTS or newer
- **Kernel**: Linux kernel 4.8+ (for VxLAN support)
- **Python**: Python 3.8+

### Required Kernel Modules
- `vxlan`
- `br_netfilter`

### Required System Commands
- `ip` (iproute2)
- `bridge` (bridge-utils)
- `iptables`

## Installation

### Quick Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd vxlan-management-system
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create required directories:
```bash
mkdir -p logs config
```

4. Load required kernel modules:
```bash
sudo modprobe vxlan
sudo modprobe br_netfilter
```

### System Installation (Ubuntu)

For production deployment, use the installation script:

```bash
sudo ./scripts/install.sh
```

This will:
- Install system dependencies
- Create configuration directories
- Install the application to `/opt/gind-vxlan`
- Configure systemd service
- Set up firewall rules

## Usage

### Command Line Interface

#### Basic Tunnel Operations

Create a tunnel:
```bash
python main.py tunnel add --vni 100 --local-ip 192.0.2.1 --remote-ip 198.51.100.1
```

List all tunnels:
```bash
python main.py tunnel list --format table
```

Delete a tunnel:
```bash
python main.py tunnel delete --tunnel-id vxlan100
```

Show tunnel details:
```bash
python main.py tunnel show --tunnel-id vxlan100 --format yaml
```

#### Topology Management

Create a hub-spoke topology:
```bash
python main.py topology create --type hub-spoke --config examples/hub-spoke.yaml
```

Plan topology (dry run):
```bash
python main.py topology create --type full-mesh --config examples/full-mesh.yaml --dry-run
```

#### System Operations

Check system status:
```bash
python main.py status
```

Recover tunnel state:
```bash
python main.py recover
```

### REST API

Start the API service:
```bash
python main.py api
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

#### API Endpoints

- **Health Check**: `GET /health`
- **List Tunnels**: `GET /api/v1/tunnels`
- **Create Tunnel**: `POST /api/v1/tunnels`
- **Get Tunnel**: `GET /api/v1/tunnels/{tunnel_id}`
- **Delete Tunnel**: `DELETE /api/v1/tunnels/{tunnel_id}`
- **Create Topology**: `POST /api/v1/topology`
- **System Status**: `GET /api/v1/status`
- **State Recovery**: `POST /api/v1/recover`

### Example API Usage

Create a tunnel:
```bash
curl -X POST "http://localhost:8000/api/v1/tunnels" \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 100,
    "local_ip": "192.0.2.1",
    "remote_ip": "198.51.100.1",
    "bridge_name": "br-lan",
    "mtu": 1450
  }'
```

### Site-to-Site Connection

**Site A Setup with Layer 3 connectivity:**
```bash
# Create VxLAN tunnel with bridge IP for Layer 3
python main.py cli tunnel create \
  --vni 1001 \
  --local-ip 203.0.113.10 \
  --remote-ip 198.51.100.20 \
  --bridge-ip 10.0.1.1 \
  --bridge-netmask 24 \
  --label "site-a-to-site-b"
```

**Site B Setup:**
```bash
# Create corresponding tunnel on Site B
python main.py cli tunnel create \
  --vni 1001 \
  --local-ip 198.51.100.20 \
  --remote-ip 203.0.113.10 \
  --bridge-ip 10.0.1.2 \
  --bridge-netmask 24 \
  --label "site-b-to-site-a"
```

**Via API (with Layer 3):**
```bash
curl -X POST http://localhost:8000/api/v1/tunnels \
  -H "Content-Type: application/json" \
  -d '{
    "vni": 1001,
    "local_ip": "203.0.113.10",
    "remote_ip": "198.51.100.20",
    "interface_name": "vxlan1001",
    "bridge_name": "br-lan",
    "bridge_ip": "10.0.1.1",
    "bridge_netmask": "24",
    "label": "site-a-to-site-b"
  }'
```

**Layer 2 Extension (bridging local interfaces):**
```bash
# Create tunnel without IP (Layer 2 only)
python main.py cli tunnel create \
  --vni 1001 \
  --local-ip 203.0.113.10 \
  --remote-ip 198.51.100.20

# Add local interface to bridge for L2 extension
ip link set eth1 master br-lan
```

## Configuration

### Application Configuration

Edit `config/app_config.yaml`:

```yaml
# API Configuration
api_port: 8000
log_level: "INFO"
log_file: "./logs/gind-tunnels.log"

# Default Values
default_mtu: 1450
default_bridge: "br-lan"
default_physical_interface: "eth0"

# Security Configuration
encryption_enabled: false
default_encryption: "none"
```

### Topology Configuration Examples

#### Hub-Spoke Topology
```yaml
# examples/hub-spoke.yaml
nodes:
  site-a:
    wan_ip: "192.0.2.1"
    physical_interface: "eth0"
  site-b:
    wan_ip: "198.51.100.1"
    physical_interface: "eth0"
  site-c:
    wan_ip: "203.0.113.1"
    physical_interface: "eth0"

hub:
  node: "site-a"

base_vni: 100
bridge_name: "br-lan"
mtu: 1450
```

#### Full-Mesh Topology
```yaml
# examples/full-mesh.yaml
nodes:
  site-a:
    wan_ip: "192.0.2.1"
  site-b:
    wan_ip: "198.51.100.1"
  site-c:
    wan_ip: "203.0.113.1"

base_vni: 200
bridge_name: "br-lan"
```

#### Partial-Mesh Topology
```yaml
# examples/partial-mesh.yaml
nodes:
  site-a:
    wan_ip: "192.0.2.1"
  site-b:
    wan_ip: "198.51.100.1"
  site-c:
    wan_ip: "203.0.113.1"

connections:
  - node1: "site-a"
    node2: "site-b"
  - node1: "site-b"
    node2: "site-c"

base_vni: 300
```

## Architecture

### Core Components

- **VxLANManager**: Central tunnel lifecycle management
- **CLI Interface**: Click-based command-line interface
- **REST API**: FastAPI-based web service
- **TopologyManager**: Multi-node coordination system
- **ConfigManager**: Configuration and persistence layer
- **Logger**: IPFIX-compliant structured logging

### Data Flow

1. **Configuration**: YAML-based configuration files store tunnel definitions
2. **Validation**: Input validation for VNI ranges, IP addresses, and parameters
3. **Execution**: System commands create VxLAN interfaces and bridge configurations
4. **Persistence**: Configuration saved to YAML files for recovery
5. **Monitoring**: Structured logging with tunnel lifecycle events

## Systemd Service

For production deployment, the system can run as a systemd service:

```bash
# Start the service
sudo systemctl start gind-vxlan

# Enable auto-start
sudo systemctl enable gind-vxlan

# Check status
sudo systemctl status gind-vxlan

# View logs
sudo journalctl -u gind-vxlan -f
```

## Security Considerations

### Network Security
- Configure firewall rules for VxLAN port (4789/UDP)
- Restrict API access (default port 8000/TCP)
- Use IPSec or other encryption for tunnel security

### System Security
- Run with appropriate privileges for network configuration
- Secure configuration files and API endpoints
- Monitor tunnel activity through structured logs

## Troubleshooting

### Common Issues

1. **Kernel Module Not Found**
   ```bash
   sudo modprobe vxlan
   ```

2. **Permission Denied**
   - Ensure running with sufficient privileges for network operations
   - Check file permissions for configuration directories

3. **Interface Already Exists**
   - Use `tunnel list` to check existing tunnels
   - Delete conflicting tunnels or use different VNI values

4. **MTU Issues**
   - Adjust MTU values based on underlay network
   - Check physical interface MTU settings

### Debug Mode

Enable debug logging:
```bash
python main.py --log-level DEBUG tunnel list
```

Check system requirements:
```bash
python -c "from vxlan_manager.utils import check_system_requirements; print(check_system_requirements())"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review system requirements
- Check logs in `./logs/gind-tunnels.log`
- Verify kernel module availability