
#!/bin/bash
# Site B VxLAN Tunnel Setup Commands
# Run these commands on Site B's CPE/router

echo "Setting up VxLAN tunnel on Site B..."

# Create VxLAN interface
ip link add vxlan1001 type vxlan \
    id 1001 \
    local 198.51.100.20 \
    remote 203.0.113.10 \
    dev eth0 \
    dstport 4789

# Bring up the VxLAN interface
ip link set vxlan1001 up

# Create bridge if it doesn't exist
ip link add br-lan type bridge 2>/dev/null || echo "Bridge br-lan already exists"
ip link set br-lan up

# Add VxLAN interface to bridge
ip link set vxlan1001 master br-lan

# Set MTU
ip link set vxlan1001 mtu 1450

# Optional: Add local LAN interface to bridge for L2 extension
# ip link set eth1 master br-lan  # Uncomment if extending L2 across sites

echo "Site B VxLAN tunnel configuration complete!"
echo "Tunnel interface: vxlan1001"
echo "Local endpoint: 198.51.100.20"
echo "Remote endpoint: 203.0.113.10"
echo "VNI: 1001"

# Verify configuration
echo -e "\nVerifying tunnel status:"
ip link show vxlan1001
ip link show br-lan
