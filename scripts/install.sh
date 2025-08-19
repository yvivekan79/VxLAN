#!/bin/bash
set -e

# VxLAN Tunnel Management System Installation Script

echo "Installing VxLAN Tunnel Management System..."

# Configuration
INSTALL_DIR="/opt/gind-vxlan"
CONFIG_DIR="/etc/gind-vxlan"
LOG_DIR="/var/log"
SERVICE_FILE="/etc/systemd/system/gind-vxlan.service"
BINARY_LINK="/usr/local/bin/gind-vxlan"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

# Check system requirements
echo "Checking system requirements..."

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" != "ubuntu" ]; then
        echo "Warning: This system is designed for Ubuntu. Current OS: $ID"
    fi
    
    if [ "${VERSION_ID%.*}" -lt 22 ]; then
        echo "Warning: Ubuntu 22.04 LTS or newer is recommended. Current version: $VERSION_ID"
    fi
else
    echo "Warning: Could not detect OS version"
fi

# Check kernel version
KERNEL_VERSION=$(uname -r | cut -d. -f1,2)
KERNEL_MAJOR=$(echo $KERNEL_VERSION | cut -d. -f1)
KERNEL_MINOR=$(echo $KERNEL_VERSION | cut -d. -f2)

if [ "$KERNEL_MAJOR" -lt 4 ] || ([ "$KERNEL_MAJOR" -eq 4 ] && [ "$KERNEL_MINOR" -lt 8 ]); then
    echo "Error: Kernel 4.8+ is required for VxLAN support. Current: $(uname -r)"
    exit 1
fi

echo "Kernel version check passed: $(uname -r)"

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    iproute2 \
    bridge-utils \
    iptables \
    curl \
    wget \
    systemd

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --system \
    fastapi \
    uvicorn \
    click \
    pyyaml \
    pydantic \
    ipaddress

# Load required kernel modules
echo "Loading kernel modules..."
modprobe vxlan || echo "Warning: Could not load vxlan module"
modprobe br_netfilter || echo "Warning: Could not load br_netfilter module"

# Add modules to autoload
echo "vxlan" >> /etc/modules
echo "br_netfilter" >> /etc/modules

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Copy application files
echo "Installing application files..."
if [ -d "vxlan_manager" ]; then
    cp -r vxlan_manager "$INSTALL_DIR/"
    cp main.py "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/main.py"
else
    echo "Error: vxlan_manager directory not found"
    exit 1
fi

# Copy configuration files
echo "Installing configuration files..."
if [ -f "config/app_config.yaml" ]; then
    cp config/app_config.yaml "$CONFIG_DIR/"
fi

if [ -f "config/tunnels.yaml" ]; then
    cp config/tunnels.yaml "$CONFIG_DIR/"
fi

# Set permissions
echo "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chown -R root:root "$CONFIG_DIR"
chmod -R 644 "$CONFIG_DIR"/*.yaml
chmod 755 "$CONFIG_DIR"

# Create log file
touch "$LOG_DIR/gind-tunnels.log"
chown root:root "$LOG_DIR/gind-tunnels.log"
chmod 644 "$LOG_DIR/gind-tunnels.log"

# Create binary link
echo "Creating command link..."
cat > "$BINARY_LINK" << 'EOF'
#!/bin/bash
cd /opt/gind-vxlan
python3 main.py "$@"
EOF
chmod +x "$BINARY_LINK"

# Install systemd service
echo "Installing systemd service..."
if [ -f "systemd/gind-vxlan.service" ]; then
    cp systemd/gind-vxlan.service "$SERVICE_FILE"
    systemctl daemon-reload
    systemctl enable gind-vxlan.service
    echo "Systemd service installed and enabled"
else
    echo "Warning: Service file not found, skipping systemd installation"
fi

# Configure firewall (if ufw is installed)
if command -v ufw >/dev/null 2>&1; then
    echo "Configuring firewall..."
    ufw allow 4789/udp comment "VxLAN"
    ufw allow 8000/tcp comment "VxLAN API"
    echo "Firewall configured for VxLAN (port 4789/udp) and API (port 8000/tcp)"
fi

# Test installation
echo "Testing installation..."
cd "$INSTALL_DIR"

# Test CLI
if python3 main.py tunnel list >/dev/null 2>&1; then
    echo "CLI test passed"
else
    echo "Warning: CLI test failed"
fi

# Test configuration
if python3 -c "from vxlan_manager.config import load_app_config; load_app_config()" >/dev/null 2>&1; then
    echo "Configuration test passed"
else
    echo "Warning: Configuration test failed"
fi

echo ""
echo "=============================================="
echo "VxLAN Tunnel Management System installed successfully!"
echo "=============================================="
echo ""
echo "Usage:"
echo "  Command Line: gind-vxlan tunnel --help"
echo "  API Service:  systemctl start gind-vxlan"
echo "  Check Status: systemctl status gind-vxlan"
echo ""
echo "Configuration:"
echo "  App Config:    $CONFIG_DIR/app_config.yaml"
echo "  Tunnels:       $CONFIG_DIR/tunnels.yaml"
echo "  Logs:          $LOG_DIR/gind-tunnels.log"
echo ""
echo "Examples:"
echo "  gind-vxlan tunnel add --vni 100 --local-ip 192.0.2.1 --remote-ip 198.51.100.1"
echo "  gind-vxlan tunnel list"
echo "  gind-vxlan topology create --type hub-spoke --config topology.yaml"
echo ""
echo "API Documentation: http://localhost:8000/docs (after starting service)"
echo ""

# Offer to start the service
read -p "Start the VxLAN service now? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start gind-vxlan
    echo "Service started. Check status with: systemctl status gind-vxlan"
    echo "API documentation available at: http://localhost:8000/docs"
fi

echo "Installation complete!"
