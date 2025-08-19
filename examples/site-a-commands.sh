
#!/bin/bash
# Site A VxLAN Tunnel Setup Commands
# Run these commands on Site A's CPE/router

echo "Setting up VxLAN tunnel on Site A..."

# Create VxLAN interface
ip link add vxlan1001 type vxlan \
    id 1001 \
    local 203.0.113.10 \
    remote 198.51.100.20 \
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

echo "Site A VxLAN tunnel configuration complete!"
echo "Tunnel interface: vxlan1001"
echo "Local endpoint: 203.0.113.10"
echo "Remote endpoint: 198.51.100.20"
echo "VNI: 1001"

# Verify configuration
echo -e "\nVerifying tunnel status:"
ip link show vxlan1001
ip link show br-lan
